"""Ingestion reads only documented source HTTP methods, never fixtures or tables."""
import hashlib
import json
import re
from .models import KnowledgeDocument, Metadata, Chunk
from ..application.models import WorkflowError


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def adapt(raw):
    content = raw['content']
    actual = hashlib.sha256(content.encode()).hexdigest()
    if actual != raw['content_hash']:
        raise WorkflowError('KNOWLEDGE_SOURCE_HASH_MISMATCH')
    heading = re.search(r'^#\s+(.+)$', content, re.M)
    title = raw.get('title') or (heading.group(1).strip() if heading else raw['id'])
    metadata = Metadata(document_id=raw['id'], title=title,
        title_origin='source title' if raw.get('title') else 'source heading' if heading else 'document ID fallback',
        document_type=raw['document_type'], document_version=raw['document_version'],
        program_id=raw['program_id'], customer_id=raw['customer_id'],
        source_system=raw['owning_system'], approval_status=raw['status'],
        content_version=raw['content_version'], content_hash=actual, updated_at=raw['updated_at'],
        **{key: raw[key] for key in ('product','configuration_id','owner_team','effective_date','superseded_by',
            'applicable_workflows','record_version','access_roles','historical') if key in raw})
    return KnowledgeDocument(metadata=metadata, content=content)


class SourceCorpus:
    def __init__(self, read): self.read = read

    def documents(self, customer, program):
        rows = self.read.get_documents(program)['items']
        if len(rows) > 500: raise WorkflowError('KNOWLEDGE_CORPUS_LIMIT')
        docs = []
        for row in rows:
            if (row.get('customer_id'), row.get('program_id')) != (customer, program): continue
            raw = self.read.get_document(row['id'])
            if (raw.get('customer_id'), raw.get('program_id')) != (customer, program):
                raise WorkflowError('KNOWLEDGE_SOURCE_SCOPE_MISMATCH')
            if raw['content_hash'] != row['content_hash']:
                raise WorkflowError('KNOWLEDGE_SOURCE_CHANGED')
            docs.append(adapt(raw))
        return sorted(docs, key=lambda d: d.metadata.document_id)


def chunk(document):
    """Heading-aware, at most ~450 words; long sections split at paragraphs/sentences.

    Ordinal + section + identity/version/hash make IDs deterministic and immutable.
    """
    sections = []
    heading, lines = None, []
    for line in document.content.splitlines():
        match = re.match(r'^#{1,6}\s+(.+)', line)
        if match:
            if lines: sections.append((heading, '\n'.join(lines).strip()))
            heading, lines = match.group(1).strip(), [line]
        else: lines.append(line)
    if lines: sections.append((heading, '\n'.join(lines).strip()))
    result = []
    for section, text in sections:
        pieces, current = [], ''
        for paragraph in re.split(r'\n\s*\n', text):
            units = [paragraph] if len(paragraph.split()) <= 450 else re.split(r'(?<=[.!?])\s+', paragraph)
            for unit in units:
                # Only a single oversized sentence needs bounded word splitting.
                words = unit.split()
                for start in range(0, max(1, len(words)), 450):
                    part = unit if len(words) <= 450 else ' '.join(words[start:start+450])
                    if current and len((current+' '+part).split()) > 450:
                        pieces.append(current); current = ''
                    current = (current+'\n\n'+part).strip()
        if current: pieces.append(current)
        for passage in pieces:
            ordinal = len(result)
            meta = document.metadata
            cid = 'chunk_' + digest([meta.document_id,meta.document_version,meta.content_version,meta.content_hash,section,ordinal])[:32]
            result.append(Chunk(chunk_id=cid,metadata=meta,section=section,passage=passage,ordinal=ordinal))
    return result

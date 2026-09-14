import os
from dataclasses import dataclass
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    db_path: Path
    storage_root: Path
    demo_mode: bool

    @classmethod
    def environment(cls):
        return cls(Path(os.environ.get('DEMO_DB', str(PROJECT / '.demo/enterprise.sqlite3'))).absolute(),
                   PROJECT / '.demo', os.environ.get('DEMO_MODE') == 'true')

    def validate(self, existing=False):
        if not self.demo_mode:
            raise ValueError('DEMO_MODE=true is required')
        target = self.db_path.absolute()
        storage = self.storage_root.absolute()
        if not storage.is_relative_to(PROJECT) or not target.is_relative_to(storage) or target == storage:
            raise ValueError('Database must be inside configured project demo storage')
        for path in (target, *target.parents):
            if path.is_symlink():
                raise ValueError('Symlink database targets or parents are refused')
        if target.exists():
            if not target.is_file() or target.stat().st_nlink != 1:
                raise ValueError('Database must be a regular file with one hard link')
        elif existing:
            raise ValueError('Initialize the demo database first')
        return target

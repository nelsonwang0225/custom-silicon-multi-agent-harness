// Local illustrative concepts only; never imported by the production frontend.
import { fileURLToPath } from 'node:url';
const path = value => fileURLToPath(new URL(value, import.meta.url));
export default {
  root: path('./'),
  resolve: { alias: Object.fromEntries(['react', 'react-dom', 'lucide-react'].map(name => [name, path('../../../mock_apps_ui/node_modules/' + name)])) },
  server: { host: '127.0.0.1', port: 5205, strictPort: true, fs: { allow: [path('../../../')] } },
};

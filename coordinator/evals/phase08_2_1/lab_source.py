"""Developer-only failed lab observation fixture. No HTTP fault controls."""
import uvicorn
from mock_enterprise.app import create_app
from mock_enterprise.db import Store

original_insert = Store.insert

def failed_lab_observation(self, kind, data):
    if kind == 'validation.result' and data['id'].startswith('result-'):
        data = {**data, 'criteria_passed': False}
    return original_insert(self, kind, data)

if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser(); parser.add_argument('--port',type=int,required=True)
    args=parser.parse_args()
    Store.insert=failed_lab_observation
    uvicorn.run(create_app(),host='127.0.0.1',port=args.port,access_log=False)

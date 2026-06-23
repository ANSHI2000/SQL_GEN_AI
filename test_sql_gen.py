import httpx, time, json

time.sleep(2)
base = 'http://localhost:8000'

# Login
r = httpx.post(f'{base}/api/login', json={'email':'logintest2@example.com','password':'password123'}, timeout=10)
print(f'Login: {r.status_code}')

if r.status_code == 200:
    token = r.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    
    # Test generate SQL
    start = time.time()
    try:
        r2 = httpx.post(f'{base}/api/gemini/generate-sql', 
            json={'connection_id': 3, 'question': 'show all users'},
            headers=headers, timeout=35)
        elapsed = time.time() - start
        print(f'Generate SQL: {r2.status_code} ({elapsed:.1f}s)')
        if r2.status_code == 200:
            data = r2.json()
            if data.get('options'):
                count = len(data['options'])
                print(f'Options count: {count}')
                first_sql = data['options'][0]['sql']
                print(f'First SQL: {first_sql[:150]}')
            else:
                err = data.get('error', 'No options')
                print(f'Error: {err}')
        else:
            print(f'Error: {r2.text[:300]}')
    except Exception as e:
        elapsed = time.time() - start
        print(f'Timeout after {elapsed:.1f}s: {str(e)[:100]}')
import utils

sp = utils.spotipySetup()

(db, cursor) = utils.db_setup()


dicts = [
    {'name': 'ben', 'age': 15, 'male': True},
    {'name': 'caleb', 'age': 17, 'male': True},
    {'name': 'christine', 'age': 16, 'male': False}
]

lambdas = [
    lambda b: b['name'] == 'caleb',
    lambda b: b['male']
]

url = 

for lam in lambdas:
    for obj in dicts:
        if lam(obj):
            print(obj)
            break

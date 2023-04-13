import requests
import json
import sys
import argparse

ignore_types = ['Float', 'Int', 'String', 'Boolean', '__Schema', '__Type', '__TypeKind', '__Field', '__InputValue', '__EnumValue', '__Directive', '__DirectiveLocation']
ignore_kind = ['SCALAR']
introspection_query = { "query": "{__schema{queryType{name}mutationType{name}subscriptionType{name}types{...FullType}directives{name description locations args{...InputValue}}}}fragment FullType on __Type{kind name description fields(includeDeprecated:true){name description args{...InputValue}type{...TypeRef}isDeprecated deprecationReason}inputFields{...InputValue}interfaces{...TypeRef}enumValues(includeDeprecated:true){name description isDeprecated deprecationReason}possibleTypes{...TypeRef}}fragment InputValue on __InputValue{name description type{...TypeRef}defaultValue}fragment TypeRef on __Type{kind name ofType{kind name ofType{kind name ofType{kind name ofType{kind name ofType{kind name ofType{kind name ofType{kind name}}}}}}}}"}

final_output = {'Object':[], 'Query':[], 'Mutation':[], 'Enum':[], 'Union':[]}

def graphql_introspection_print_output(filter):
    if filter == None:
        filter = ['enum', 'query', 'mutation', 'union', 'object']

    if 'enum' in filter:
        print("\n--- Enums ---")
        for i in final_output['Enum']:
            print(f"\n{i['name']}: {{")
            for j in i['values']:
                print(f"   {j}")
            print("}")
    
    if 'union' in filter:
        print("\n--- Unions ---")
        for i in final_output['Union']:
            print(f"\n{i['name']}: {{")
            for j in i['values']:
                print(f"   {j}")
            print("}")

    if 'object' in filter:
        print("\n--- Objects ---")
        for i in final_output['Object']:
            print(f"\n{i['name']}: {{")
            for j in i['fields']:
                print(f"   {j['name']}: {j['type']}")
            print("}")

    if 'query' in filter:
        print("\n--- Queries ---\n")
        for i in final_output['Query']:
            print(f"{i['name']}(", end='')
            for j in i['args']:
                print(f" {j['name']}: {j['type']} ", end='')
            print(f") {{ {i['result']} }}")
    
    if 'mutation' in filter:
        print("\n--- Mutations ---\n")
        for i in final_output['Mutation']:
            print(f"{i['name']}(", end='')
            for j in i['args']:
                print(f" {j['name']}: {j['type']} ", end='')
            print(f") {{ {i['result']} }}")

def get_object_type(type):
    if (type['kind'] == 'NON_NULL'):
        return (get_object_type(type['ofType']))
    if (type['kind'] == 'LIST'):
        return (f"List({get_object_type(type['ofType'])})")
    return (type['name'] if type['name'] else type['ofType']['name'])

def graphql_introspection_parse_object(json_object):
    queryType = json_object['queryType']['name']
    mutationType = json_object['mutationType']['name']

    for i in json_object['types']:
        if i['name'] == queryType:
            for j in i['fields']:
                final_output['Query'].append({
                    'name': j['name'],
                    'args': [{'name': k['name'], 'type': get_object_type(k['type']) } for k in j['args']],
                    'result': get_object_type(j['type'])
                })
        elif i['name'] == mutationType:
            for j in i['fields']:
                final_output['Mutation'].append({
                    'name': j['name'],
                    'args': [{'name': k['name'], 'type': get_object_type(k['type']) } for k in j['args']],
                    'result': get_object_type(j['type'])
                })
        elif i['kind'] == 'ENUM':
            final_output['Enum'].append({
                'name': i['name'],
                'values': [j['name'] for j in i['enumValues']]
            })
        elif i['kind'] == 'UNION':
            final_output['Union'].append({
                'name': i['name'],
                'values': [j['name'] for j in i['possibleTypes']]
            })
        elif i['name'] not in ignore_types and i['kind'] not in ignore_kind:
            final_output['Object'].append({
                'name':i['name'],
                'type':i['kind'],
                'fields':[{'name':j['name'],'type':get_object_type(j['type'])} for j in i['fields']]
            })

def graphql_introspection_url(url, filter=None, save_file=None, headers={}, cookies={}):
    result = requests.post(url, json=introspection_query, headers=headers, cookies=cookies)
    json_result  = json.loads(result.text)['data']['__schema']
    if save_file != None:
        with open(save_file, 'w') as f:
            f.write(result.text)

    graphql_introspection_parse_object(json_result)
    graphql_introspection_print_output(filter)

def graphql_introspection_file(file, filter=None):
    fd = open(file, 'r')
    if not fd:
        sys.exit(1)
    json_result  = json.loads(fd.read())['data']['__schema']
    graphql_introspection_parse_object(json_result)
    graphql_introspection_print_output(filter)
    

def graphql_args_parser():
    parser = argparse.ArgumentParser(prog='',
                            description='',
                            epilog='')
    parser.add_argument('-u', '--url')
    parser.add_argument('-f', '--file')
    parser.add_argument('-s', '--save', help='save introspection query in a file to avoid multiple request (only with -u)')
    parser.add_argument('-H', '--header', nargs='*', help='"header_name: header_value", Add custom header to the request (only with -u)')
    parser.add_argument('-C', '--cookie', nargs='*', help='"cookie_name: cookie_value", Add custom cookie to the request (only with -u)')
    parser.add_argument('--filter', nargs='*', help='enum, union, object, query, union')
    args = parser.parse_args()

    raw_headers = args.header
    args.header = {}
    if raw_headers != None:
        for i in raw_headers:
            splitted_header = i.split(':')
            args.header[splitted_header[0].strip()] = splitted_header[1].strip()

    raw_cookies = args.cookie
    args.cookie = {}
    if raw_cookies != None:
        for i in raw_cookies:
            splitted_cookie = i.split(':')
            args.header[splitted_cookie[0].strip()] = splitted_cookie[1].strip()

    return (args)

if __name__ == "__main__":
    
    args = graphql_args_parser()
    #print(args)

    if args.save and not args.url:
        print('Bad usage, use --help')
        sys.exit(1)
    if args.url:
        if args.file:
            print('Bad usage, use --help')
            sys.exit(1)
        graphql_introspection_url(args.url, filter=args.filter, save_file=args.save, headers=args.header, cookies=args.cookie)
    elif args.file:
        graphql_introspection_file(args.file, args.filter)
    sys.exit(0)

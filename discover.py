import yaml
import os
import objects

descriptor_synonyms = ['module.yaml', 'module.yml', 'module.json']

data_repos = ['test_data/hw_repo',
              'test_data/sw_repo']

graph = []


# Scanning repos for modules descriptors and parse them
descriptors = {}
for repo in data_repos:
    for dir in os.walk(repo):
        for file in dir[2]:
            if file in descriptor_synonyms:
                descr_name = dir[0]+'\\'+file
                descriptor = None
                with open(descr_name, 'r') as stream:
                    try:
                        descriptor = yaml.safe_load(stream)
                    except yaml.YAMLError as exc:
                        print('\nError while parsing module file:')
                        print(exc)
                        print('\n')
                if descriptor:
                    descriptors[descr_name] = descriptor

for file, descriptor in descriptors.items():
    graph.append(objects.Module.parse(None, file, descriptor))
print(graph)

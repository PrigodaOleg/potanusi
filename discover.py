import yaml
import os
import objects

descriptor_synonyms = ['module.yaml', 'module.yml', 'module.json']

data_repos = ['test_data/hw_repo',
              'test_data/sw_repo']

modules = []

# Scanning repos for modules descriptors
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

# Parse them
for file, descriptor in descriptors.items():
    modules.append(objects.Module.parse(None, file, descriptor))

# Make all possible connections between the modules
for module in modules:
    for link_module in modules:
        if module != link_module:
            module.connect(link_module)
print(modules)

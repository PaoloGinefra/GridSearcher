import yaml

# Open and read YAML file
with open("test.yaml", "r") as file:
    config = yaml.safe_load(file)

print(config)

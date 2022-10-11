import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

class MyClass:
    def __init__(self):
        self.name = ""
        self.sad = False
        self.is_true = True

if __name__ == '__main__':
    my_class = yaml.load("""
    !!python/object:test_load_class_from_yaml.MyClass
    name: Andrew
    sad: True
    is_true: False
    """, Loader=Loader)
    print(my_class.name, my_class.sad, my_class.is_true)
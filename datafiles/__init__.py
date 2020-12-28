
def get(name):
    reader = __loader__.get_resource_reader(__name__)
    return reader.open_resource(name)

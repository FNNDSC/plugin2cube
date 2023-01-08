str_about = '''
    The behavior module codifies the operational/dynamic behavior of this
    plugin.

    Primary behaviors include some conditional logic over the space of
    input objects, and triggering a resultant operation -- usually this means
    copying the object into a child plugin, and then running a pipeline
    on the result of that copy-to-child.

    For now, this class is mostly dummy filler.
'''

def unconditionalPass(str_object: str) -> bool:
    '''
    A dummy fall through function that always returns True.
    '''
    return True

class Filter:
    '''
    An abstraction for evaluating a "condition" on some "object".
    '''

    def __init__(self, *args, **kwargs):
        # point this to a function with signature
        # <filterOp>(<str_object> : str) : bool
        self.filterOp = None

    def obj_pass(self, str_object: str) -> bool:
        return self.filterOp(str_object)
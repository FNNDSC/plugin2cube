str_about = '''
    A simple class that provides rudimentary filtering on some input
    directory for files conforming to some pattern. The primary purpose
    of this class is to provide an alternative to the built-in chris_plugin
    'PathMapper' object.
'''


from    argparse                import ArgumentParser, Namespace
from    pathlib                 import Path
import  pfmisc
import  glob
import  os

class   PathFilter:
    '''
    A simple filter class that operates on directories to catalog
    some filtered subset of the input filesystem space.
    '''

    def __init__(self, inputdir, outputdir, *args, **kwargs):
        """Main constructor
        """

        self.inputdir       : Path          = inputdir
        self.outputdir      : Path          = outputdir
        self.glob           : str           = '*'
        self.l_files        : list          = []
        self.LOG            : pfmisc.debug  = None
        self.b_filesOnly    : bool          = False

        for k,v in kwargs.items():
            if k == 'glob'          : self.glob         = v
            if k == 'logger'        : self.LOG          = v
            if k == 'only_files'    : self.b_filesOnly  = True

        self.inputdir_filter(self.inputdir)

    def __iter__(self):
        return PathIterator(self)

    def log(self, message, **kwargs):
        if self.LOG: self.LOG(message)

    def inputdir_filter(self, input: Path) -> list:
        '''
        Filter the files in Path according to the passed options.pattern --
        mostly for debugging
        '''

        self.LOG("Parent directory contains at root level")
        l_ls = [self.LOG(f) for f in os.listdir(str(input))]
        self.LOG("Filtering files in %s containing '%s'" % (str(input), self.glob))
        str_glob : str  = '%s/%s' % (str(self.inputdir), self.glob)
        self.LOG("glob = %s" % str_glob)

        self.l_files    = glob.glob(str_glob)

        l_glob = [self.LOG(f) for f in self.l_files]
        return self.l_files

class   PathIterator:
    '''
    An iterator over the PathFilter class
    '''

    def __init__(self, pathfilter):

        self._pathfilter    = pathfilter
        self._index         = 0

    def __next__(self):
        '''
        Iterate over the PathFilter self.files list
        '''
        if self._index < len(self._pathfilter.l_files):
            result      = (self._pathfilter.l_files[self._index])
            self._index += 1
            return (result, self._pathfilter.outputdir)
        raise StopIteration

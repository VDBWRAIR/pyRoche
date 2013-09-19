class Newbler( object ):
    def addRun( self, **kwargs ):
        '''
            Wraps around the addRun command
            Usage: addRun [options: (-p | -np) -lib
                    (-mcf | -custom)] [projDir] [MIDList@]filedesc
        '''
        pass

    def runProject( self ):
        pass

class NewblerMapping( Newbler ):
    def newMapping( self ):
        pass

    def setRef( self ):
        pass

class NewblerAssembly( Newbler ):
    def newAssembly( self ):
        pass

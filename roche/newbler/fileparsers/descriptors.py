class DescriptorBase( object ):
    def __init__( self, name ):
        '''
            Keep the name of the attribute as well as the underscore name
            to store the value under to avoid recursion
        '''
        self.name = name
        self.store_name = "_{}".format( name )
    def __get__( self, inst, klass ):
        return getattr( inst, self.store_name )
    def __set__( self, inst, value ):
        setattr( inst, self.store_name, value )

class ValidSetDescriptor( DescriptorBase ):
    ''' Allow only values from a defined set and/or types '''
    def __init__( self, name, valid_values='ANY', valid_types='ANY' ):
        super( ValidSetDescriptor, self ).__init__( name )
        self.valid_values = valid_values
        self.valid_types = valid_types
    def __set__( self, inst, value ):
        if self.valid_types == 'ANY' or type( value ) in self.valid_types:
            if self.valid_values == 'ANY' or value in self.valid_values:
                setattr( inst, self.store_name, value )
            else:
                raise ValueError( "{} is not a valid value. Not in {}".format( value, self.valid_values ) )
        else:
            raise ValueError( "{} is not a valid type. Not in {}".format( type(value), self.valid_types ) )

class NumberDescriptor( ValidSetDescriptor ):
    ''' Generic Number Descriptor '''
    def __init__( self, name ):
        super( NumberDescriptor, self ).__init__( name, valid_types=(int,float) )

class Nucleotide( ValidSetDescriptor ):
    '''
        Valid simple Nucleotide base checker
        Probably should use Biopython to check this but I'm lazy
    '''
    def __init__( self, name ):
        valid_bases = ('A','G','T','C','N','-')
        super( Nucleotide, self ).__init__( name, valid_bases )

class GreaterThanZero( NumberDescriptor ):
    ''' Number greater than zero '''
    def __set__( self, inst, value ):
        if value <= 0:
            raise ValueError( "{} is not greater than zero".format( value ) )
        else:
            super( GreaterThanZero, self ).__set__( inst, value )

class GreaterThanEqualZero( NumberDescriptor ):
    ''' Number greater than zero '''
    def __set__( self, inst, value ):
        if value < 0:
            raise ValueError( "{} is not greater than or equal to zero".format( value ) )
        else:
            super( GreaterThanEqualZero, self ).__set__( inst, value )

class GreaterThanZeroFloat( GreaterThanZero ):
    ''' Force value to be a float '''
    def __set__( self, inst, value ):
        super( GreaterThanZeroFloat, self ).__set__( inst, float( value ) )

class GreaterThanZeroPercent( GreaterThanZeroFloat ):
    ''' Force value to be a float '''
    def __set__( self, inst, value ):
        super( GreaterThanZeroFloat, self ).__set__( inst, float( value.replace( '%','' ) ) )
    def __get__( self, inst, value ):
        return '{}%'.format( super( GreaterThanZeroPercent, self ).__get__( inst, value ) )

class GreaterThanZeroInt( GreaterThanZero ):
    ''' Force value to be a Int '''
    def __set__( self, inst, value ):
        super( GreaterThanZeroInt, self ).__set__( inst, int( value ) )

class GreaterThanEqualZeroFloat( GreaterThanEqualZero ):
    ''' Force value to be a float '''
    def __set__( self, inst, value ):
        super( GreaterThanEqualZeroFloat, self ).__set__( inst, float( value ) )

class GreaterThanEqualZeroPercent( GreaterThanEqualZeroFloat ):
    ''' Force value to be a float '''
    def __set__( self, inst, value ):
        super( GreaterThanEqualZeroFloat, self ).__set__( inst, float( value.replace( '%','' ) ) )
    def __get__( self, inst, value ):
        return '{}%'.format( super( GreaterThanEqualZeroPercent, self ).__get__( inst, value ) )

class GreaterThanEqualZeroInt( GreaterThanEqualZero ):
    ''' Force value to be a Int '''
    def __set__( self, inst, value ):
        super( GreaterThanEqualZeroInt, self ).__set__( inst, int( value ) )

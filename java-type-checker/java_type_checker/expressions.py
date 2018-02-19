# -*- coding: utf-8 -*-

from .types import Type


class Expression(object):
    """
    AST for simple Java expressions. Note that this package deal only with compile-time types;
    this class does not actually _evaluate_ expressions.
    """

    def static_type(self):
        """
        Returns the compile-time type of this expression, i.e. the most specific type that describes
        all the possible values it could take on at runtime. Subclasses must implement this method.
        """
        raise NotImplementedError(type(self).__name__ + " must implement static_type()")

    def check_types(self):
        """
        Validates the structure of this expression, checking for any logical inconsistencies in the
        child nodes and the operation this expression applies to them.
        """
        raise NotImplementedError(type(self).__name__ + " must implement check_types()")


class Variable(Expression):
    """ An expression that reads the value of a variable, e.g. `x` in the expression `x + 5`.
    """
    def __init__(self, name, declared_type):
        self.name = name                    #: The name of the variable
        self.declared_type = declared_type  #: The declared type of the variable (Type)

    def static_type(self):
        """
        Returns the compile-time type of this expression.
        """
        return self.declared_type

    def check_types(self):
        if self.declared_type != self.declared_type:
            raise TypeError(
                "Wrong type of argument for variable creation: expected {}, got {}".format(type(self.name), self.declared_type)
            )


class Literal(Expression):
    """ A literal value entered in the code, e.g. `5` in the expression `x + 5`.
    """
    def __init__(self, value, type):
        self.value = value  #: The literal value, as a string
        self.type = type    #: The type of the literal (Type)

    def static_type(self):
        """
        Returns the compile-time type of this expression, i.e. the most specific type that describes
        all the possible values it could take on at runtime. Subclasses must implement this method.
        """
        return self.type


class NullLiteral(Literal):
    def __init__(self):
        super().__init__("null", Type.null)

    def static_type(self):
        """
        Returns the compile-time type of this expression, i.e. the most specific type that describes
        all the possible values it could take on at runtime. Subclasses must implement this method.
        """
        return Type.null


class MethodCall(Expression):
    """
    A Java method invocation, i.e. `foo.bar(0, 1, 2)`.
    """
    def __init__(self, receiver, method_name, *args):
        self.receiver = receiver        #: The object whose method we are calling (Expression)
        self.method_name = method_name  #: The name of the method to call (String)
        self.args = args                #: The method arguments (list of Expressions)

    def static_type(self):
        """
        Returns the compile-time type of this expression, i.e. the most specific type that describes
        all the possible values it could take on at runtime. Subclasses must implement this method.
        """
        return self.receiver.static_type().method_named(self.method_name).return_type

    def check_types(self):
        """
        Raises an error if the types don't check out. Doesn't return anything.
        """

        if self.receiver.static_type() in [Type.void, Type.boolean, Type.int, Type.double, Type.null]:
            raise JavaTypeError(
                "Type {0} does not have methods".format(self.receiver.static_type().name)
            )

        else:
            expected_types = self.receiver.static_type().method_named(self.method_name).argument_types
            call_name = self.receiver.declared_type.name + "." + self.method_name + "()"
            actual_types = []
            for item in self.args:
                actual_types.append(item.static_type())

            if len(actual_types) != len(expected_types):
                raise JavaTypeError(
                    "Wrong number of arguments for {0}: expected {1}, got {2}".format(
                        call_name,
                        len(expected_types),
                        len(actual_types)))

            if expected_types != actual_types:

                for i in range(0, len(expected_types)):
                    if expected_types[i] in actual_types[i].direct_supertypes:
                        actual_types[i] = expected_types[i]

                if expected_types != actual_types:
                    raise JavaTypeError(
                        "{0} expects arguments of type {1}, but got {2}".format(
                            call_name,
                            names(expected_types),
                            names(actual_types)))

class ConstructorCall(Expression):
    """
    A Java object instantiation, i.e. `new Foo(0, 1, 2)`.
    """
    def __init__(self, instantiated_type, *args):
        self.instantiated_type = instantiated_type  #: The type to instantiate (Type)
        self.args = args                            #: Constructor arguments (list of Expressions)

    def static_type(self):
        """
        Returns the compile-time type of this expression, i.e. the most specific type that describes
        all the possible values it could take on at runtime. Subclasses must implement this method.
        """
        return self.instantiated_type

    def check_types(self):

        if self.instantiated_type in [Type.void, Type.boolean, Type.int, Type.double, Type.null]:
            raise JavaTypeError(
                "Type {0} is not instantiable".format(self.instantiated_type.name)
            )

        else:
            actual_types = []
            for item in self.args:
                actual_types.append(item.static_type())
            expected_types = self.instantiated_type.constructor.argument_types

            if len(actual_types) != len(expected_types):
                raise JavaTypeError(
                    "Wrong number of arguments for {0} constructor: expected {1}, got {2}".format(
                        self.instantiated_type.name,
                        len(expected_types),
                        len(actual_types)
                    )
                )

            if actual_types != expected_types:
                raise JavaTypeError(
                    "{0} constructor expects arguments of type {1}, but got {2}".format(
                        self.instantiated_type.name,
                        names(expected_types),
                        names(actual_types) ))


class JavaTypeError(Exception):
    """ Indicates a compile-time type error in an expression.
    """
    pass


def names(named_things):
    """ Helper for formatting pretty error messages
    """
    return "(" + ", ".join([e.name for e in named_things]) + ")"



from IPython.display import IFrame

import json
import sympy
import base64

class ExpressionCollection(object):
    def get_id(self, obj):
        return self._root.get_id(obj)
    
    def config(self, **kwargs):
        for child in self._children:
            if 'config' in dir(child):
                child.config(**kwargs)
    
    def function(self, f, name=None):
        import inspect
        argspec = inspect.getfullargspec(f)
        args = argspec.args
        # attrs = tuple(self.__getattr__(a) for a in args)
        attrs = tuple(Statement(a) for a in args)
        
        if argspec.defaults:
            split = -len(argspec.defaults)
            for arg,val in zip(args[split:], argspec.defaults):
                self.__setattr__(arg, val)
            args = args[:split]

        expr = f(*attrs)
        if isinstance(expr, Boolean) or isinstance(expr, Inequality):
            expr = expr.lump

        if name is None:
            name = f.__name__
        fn = Function(name)
        self._root._cache[name] = fn

        expr = Equality(fn(*args), expr)
        self.set(expr)
        
        fn.config = expr.config
        return fn

    _desmos_fns = {
        'asin': '\\\\sin^{-1}',
        'acos': '\\\\cos^{-1}',
        'atan': '\\\\tan^{-1}',
        'atan2': '\\\\tan^{-1}',
        'arcsin': '\\\\sin^{-1}',
        'arccos': '\\\\cos^{-1}',
        'arctan': '\\\\tan^{-1}',
        'arctan2': '\\\\tan^{-1}',
    }
    
    def __getattr__(self, name):
        statement = self._root._cache.get(name, None)
        if statement is not None:
            return statement

        if name in self._desmos_fns:
            statement = self.substitute(self._desmos_fns[name], cls=Function)
        else:
            try:
                attr = sympy.__getattribute__(name)
                if not isinstance(attr, sympy.core.function.FunctionClass):
                    return attr
                statement = NativeFunction(attr)
            except AttributeError as e:
                if "module 'sympy' has no attribute" not in str(e):
                    raise
                statement = Statement(name)
        self._root._cache[name] = statement
        return statement

    def __setattr__(self, name, value):
        if name[:1] == '_':
            return object.__setattr__(self, name, value)
        if isinstance(value, tuple) and len(value) == 2:
            value = self.point(*value)
        elif '__iter__' in dir(value):
            value = self.list(value)

        if isinstance(value, IndexedBaseValue):
            lhs = IndexedBase(name)
            self._root._cache[name] = lhs
        else:
            lhs = self.__getattr__(name)

        self.set(Equality(lhs, value))

    def activate(self):
        "Make sure this object is active before adding children."
        pass
    
    def set(self, expr, **kwargs):
        self.activate()
        if isinstance(expr, Statement):
            expr = expr >= 0
        if kwargs:
            expr.config(**kwargs)
        self._children.append(expr)
        return expr

    def abs(self, expr):
        val = Statement()
        val.expr = sympy.Abs(Statement.ref(expr))
        return val

    def sum(self, function, **kwargs):
        # pop other kwargs, if any
        if len(kwargs) > 1:
            raise ValueError(f'sum() received unknown arguments: {kwargs}')
        for key,val in kwargs.items():
            index = key
            lower,upper = val
        # index = sympy.symbols(index, cls=sympy.Idx)
        index = sympy.Symbol(index)
        expr = Statement.ref(function(index))
        lower = Statement.ref(lower)
        upper = Statement.ref(upper)
        return Statement(sympy.Sum(expr, (index,lower,upper)))

    def substitute(self, value, cls=None, **kwargs):
        if cls is None:
            cls = Statement
        var = 'v_{custom%04d}'%len(self._root._substitutions)
        self._root._substitutions[var] = value
        return cls(var, **kwargs)
    
    def point(self, *args):
        """
        Capture a point expression
            - sympy doesn't perform algebra (e.g. absolute value) on points -- it completely crashes
            - substitute a custom variable in the sympy expression, then replace this later with the latex string of the point
        """
        coords = [ sympy.latex(Statement.ref(expr)).replace('\\',r'\\') for expr in args ]
        coords = f'({", ".join(coords)})'

        return self.substitute(coords, cls=IndexedBaseValue)
    
    def list(self, values, *args, **kwargs):
        """
        Capture a list of values
            - sympy formats arrays as a matrix; we'll need to format manually
            - substitute a custom variable in the sympy expression, then replace this later with the latex string of the list
        """
        values = [ sympy.latex(Statement.ref(expr)).replace('\\',r'\\') for expr in values ]
        values = f'[{", ".join(values)}]'

        return self.substitute(values, cls=IndexedBaseValue)
    
    def range(self, *args):
        """
        Convert a range from native python to native desmos
            - substitute a custom variable in the sympy expression, then replace this later with the latex string of the range
        """
        bounds = list(args)
        bounds[-1] -= 1 # python is exclusive, desmos is inclusive
        bounds = [ sympy.latex(Statement.ref(expr)).replace('\\',r'\\') for expr in bounds ]
        bounds = f'[{0 if len(bounds) < 2 else bounds[0]}...{bounds[-1]}]'

        return self.substitute(bounds, cls=IndexedBaseValue)

class Calculator(ExpressionCollection):
    def __init__(self, size=None, **kwargs):
        """
        Arguments:
            size - iframe dimensions as tuple (width,height)
            url - location of Desmos library
            url_fmt - location of Desmos library, parameterized with {"rev", "key"}
            key - Desmos key
            rev - Version of Desmos library
            **others - remaining kwargs are forwarded to Desmos as API options (see https://www.desmos.com/api/v1.9/docs/index.html)
        """
        if size:
            self._width,self._height = size
        else:
            self._width = 1080
            self._height = 360

        kwargs,self._url = self.url_from_kwargs(**kwargs)

        # Overried default Desmos options, unless specified by user
        ## kwargs.setdefault('expressionsCollapsed', True)
        self._options = json.dumps(kwargs)

        self._root = self
        self._cache = dict([(var,Statement(var)) for var in ('x','y','r','theta')])
        self._substitutions = {}
        for var in ('pi','e'):
            self.substitute(var)
        self._customs = dict(self._substitutions)
        self.clear(init=True)
        self._bounds = None

    def clear(self, init=False):
        self._next_id = 0
        self._obj_ids = {}
        if not init:
            for folder in self._folders:
                folder.clear()            
            self._substitutions = dict(self._customs)
        self._folders = []
        self._children = []

    def url_from_kwargs(self, **kwargs):
        url = kwargs.pop('url', None)
        if not url:
            url_fmt = kwargs.pop('url_fmt', 'https://www.desmos.com/api/%(rev)s/calculator.js?apiKey=%(key)s')
            rev = kwargs.pop('rev', 'v1.10')
            key = kwargs.pop('key', 'dcb31709b452b1cf9dc26972add0fda6')
            url = url_fmt % {'rev': rev, 'key': key}
        return kwargs,url

    def folder(self, name):
        folder = Folder(parent=self, name=name)
        self._children.append(folder)
        self._folders.append(folder)
        return folder

    def activateFolder(self, folder):
        if folder not in self._folders:
            self._children.append(folder)
            self._folders.append(folder)            

    def get_id(self, obj):
        """
        As the root of the tree, Calculator tracks the ID of each node
        as it is added to the HTML.
        """
        if obj not in self._obj_ids:
            self._obj_ids[obj] = self._next_id
            self._next_id += 1
        return self._obj_ids[obj]

    def bounds(self, left=0, right=0, bottom=10, top=10):
        self._bounds = (left, right, bottom, top)
    
    @property
    def html(self):
        html = []
        for child in self._children:
            self.get_id(child)
            html.append(child.html)
        html = '\n  '.join(html)
        for key,sub in self._root._substitutions.items():
            html = html.replace(key, sub)
        tree = dict((self.get_id(f),f.child_ids) for f in self._folders)
        config = []
        if self._bounds:
            config += ['calculator.setMathBounds({left: %d, right: %d, bottom: %d, top: %d});'%self._bounds]
        config = '\n    '.join(config)
        return html_fmt(self._url, html, self._options, tree, config)
    
    def save(self, filename, clear=True):
        with open(filename, 'w') as f:
            f.write(self.html)
        if clear:
            self.clear()
    
    def show(self, clear=True):
        data = base64.b64encode(self.html.encode('utf-8')).decode('utf-8')
        url = f'data:text/html;base64,{data}'
        display(IFrame(url, width=self._width, height=self._height))
        if clear:
            self.clear()

class Folder(ExpressionCollection):
    def __init__(self, parent, name):
        self._root = parent
        self._parent = parent
        self._name = name
        self.clear()

    def clear(self):
        self._children = []
        self._child_ids = None

    def activate(self):
        self._parent.activateFolder(self)

    @property
    def html(self):
        # Reserve and save ids of children
        self._child_ids = list(self._root.get_id(child) for child in self._children)
        html = ["calculator.setExpression({type: 'text', text: %(name)s});"%{'name':repr(self._name)}]
        html += list(child.html for child in self._children)
        return '\n    '.join(html)

    @property
    def child_ids(self):
        return self._child_ids

class Expression(object):
    def config(self, **kwargs):
        try:
            self.state.update(kwargs)
        except:
            self.state = kwargs
        
    @property
    def html(self):
        expr = {'latex': str(self)}
        if 'state' in dir(self):
            expr.update(self.state)
        return f'calculator.setExpression({json.dumps(expr)});'

class Statement(Expression):
    def __init__(self, value=None):
        if isinstance(value, str):
            value = sympy.Symbol(value)
        self.expr = value

    @classmethod
    def from_value(cls, val):
        if isinstance(val, Statement):
            return val
        result = Statement()
        result.expr = val
        return result
    
    @staticmethod
    def ref(val):
        if isinstance(val, Statement):
            return val.expr
        return val

    def __eq__(self, other):
        return Equality(self.expr, Statement.ref(other))

    def __lt__(self, other):
        return LessThan(self.expr, Statement.ref(other))
    
    def __le__(self, other):
        return LessEqual(self.expr, Statement.ref(other))
    
    def __gt__(self, other):
        return GreaterThan(self.expr, Statement.ref(other))
    
    def __ge__(self, other):
        return GreaterEqual(self.expr, Statement.ref(other))
    
    def __req__(self, other):
        return Equality(Statement.ref(other), self.expr)

    def __neg__(self):
        result = Statement()
        result.expr = -self.expr
        return result

    def __add__(self, other):
        result = Statement()
        result.expr = self.expr + Statement.ref(other)
        return result

    def __radd__(self, other):
        result = Statement()
        result.expr = Statement.ref(other) + self.expr
        return result

    def __sub__(self, other):
        result = Statement()
        result.expr = self.expr - Statement.ref(other)
        return result

    def __rsub__(self, other):
        result = Statement()
        result.expr = Statement.ref(other) - self.expr
        return result

    def __mul__(self, other):
        result = Statement()
        result.expr = self.expr * Statement.ref(other)
        return result

    def __rmul__(self, other):
        result = Statement()
        result.expr = Statement.ref(other) * self.expr
        return result

    def __truediv__(self, other):
        result = Statement()
        result.expr = self.expr / Statement.ref(other)
        return result

    def __rtruediv__(self, other):
        result = Statement()
        result.expr = Statement.ref(other) / self.expr
        return result

    def __pow__(self, other):
        result = Statement()
        result.expr = self.expr ** Statement.ref(other)
        return result

    def __rpow__(self, other):
        result = Statement()
        result.expr = Statement.ref(other) ** self.expr
        return result

    def __and__(self, other):
        return (self >= 0) & other
    def __rand__(self, other):
        return other & (self >= 0)

    def __or__(self, other):
        return (self >= 0) | other
    def __ror__(self, other):
        return other | (self >= 0)

    def __xor__(self, other):
        return (self >= 0) ^ other
    def __rxor__(self, other):
        return other ^ (self >= 0)

    def __str__(self):
        return str(self.expr)

class StatementAttribute(Statement):
    def __init__(self, statement, attr):
        self._statement = statement
        self._attr = attr
        class AttrSymbol(sympy.Symbol):
            def _latex(self, printer):
                return f'{str(statement)}.{attr}'
        self.expr = AttrSymbol(f'{str(statement)}.{attr}')


class IndexedBase(Statement):
    def __init__(self, base):
        self.expr = sympy.IndexedBase(str(base))

    class Indexed(sympy.Indexed):
        def _latex(self, printer):
            tex_base = printer._print(self.base)
            tex = '{'+tex_base+'}'+'[%s]' % ','.join(
                (printer._print(i+1) for i in self.indices))
            return tex
            
    def __getitem__(self, index):
        val = Statement()
        val.expr = self.Indexed(self.expr, index)
        return val
        
    @property
    def length(self):
        return StatementAttribute(self, 'length')

class IndexedBaseValue(Statement):
    """
    Used to detect when an assignment should create an IndexedBase class.
    """
    pass

class Function(Statement):
    def __init__(self, name):
        if any(symbol in name for symbol in '<>'):
            raise ValueError(f'invalid function name "{name}"')
        desmos_name = name
        if len(name.split('_')[0]) > 1:
            desmos_name = 'f_'+name

        self.expr = sympy.Symbol(desmos_name)
        self._fn = sympy.Function(self.expr)
        
    def __call__(self, *args):
        result = self._fn(*(Statement.ref(arg) for arg in args))
        return Statement.from_value(result)

class NativeFunction(Function):
    """
    A native function is a sympy function that has the same name in Desmos.
    This allows sympy to do simplification where possible,
    **assuming** that Desmos will be able to interpret the result.
    """
    def __init__(self, fn):
        self.expr = self._fn = fn

class Inequality(Expression):
    def __init__(self, lhs, rhs):
        if isinstance(lhs, Statement):
            lhs.config = self.config
            lhs = lhs.expr
        if isinstance(rhs, Statement):
            rhs = rhs.expr
        self.lhs,self.rhs = (lhs, rhs)
        
    def __str__(self):
        return sympy.latex(self.op(self.lhs, self.rhs))

    def __and__(self, other):
        return Intersect().add(self).add(other)
    def __rand__(self, other):
        if other is not None:
            raise ValueError
        return Intersect().add(self)

    def __or__(self, other):
        return Union().add(self).add(other)
    def __ror__(self, other):
        if other is not None:
            raise ValueError
        return Union().add(self)

    def __xor__(self, other):
        return XOR().add(self).add(other)
    def __rxor__(self, other):
        if other is not None:
            raise ValueError
        return XOR().add(self)

class LessThan(Inequality):
    def __init__(self, lhs, rhs):
        super().__init__(lhs, rhs)
        self.op = sympy.Lt
        self.strict = True

    def __invert__(self):
        return GreaterEqual(self.lhs, self.rhs)
    
    @property
    def lump(self):
        """ Returns a sympy expression that is >= zero iff the original inequality is True. """
        return self.rhs - self.lhs

class LessEqual(Inequality):
    def __init__(self, lhs, rhs):
        super().__init__(lhs, rhs)
        self.op = sympy.Le
        self.strict = False

    def __invert__(self):
        return GreaterThan(self.lhs, self.rhs)
    
    @property
    def lump(self):
        """ Returns a sympy expression that is > zero iff the original inequality is True. """
        return self.rhs - self.lhs

class GreaterThan(Inequality):
    def __init__(self, lhs, rhs):
        super().__init__(lhs, rhs)
        self.op = sympy.Gt
        self.strict = True

    def __invert__(self):
        return LessEqual(self.lhs, self.rhs)
    
    @property
    def lump(self):
        """ Returns a sympy expression that is > zero iff the original inequality is True. """
        return self.lhs - self.rhs

class GreaterEqual(Inequality):
    def __init__(self, lhs, rhs):
        super().__init__(lhs, rhs)
        self.op = sympy.Ge
        self.strict = False

    def __invert__(self):
        return LessThan(self.lhs, self.rhs)
    
    @property
    def lump(self):
        """ Returns a sympy expression that is >= zero iff the original inequality is True. """
        return self.lhs - self.rhs

class Equality(Expression):
    def __init__(self, lhs, rhs):
        if isinstance(lhs, Statement):
            lhs.config = self.config
            lhs = lhs.expr
        if isinstance(rhs, Statement):
            rhs = rhs.expr
        self.expr = sympy.Eq(lhs, rhs)

    def __str__(self):
        return sympy.latex(self.expr)

class Boolean(Expression):
    def __init__(self):
        self.components = []
    def __and__(self, other):
        return Intersect().add(self).add(other)
    def __or__(self, other):
        return Union().add(self).add(other)
    def __xor__(self, other):
        return XOR().add(self).add(other)
    def add(self, component):
        if not self.components:
            self.strict = component.strict
        if isinstance(component, self.__class__):
            self.components += component.components
        elif isinstance(component, Statement):
            self.components.append(component.expr)
        else:
            self.components.append(component.lump)
        return self
    def __str__(self):
        op = sympy.Gt if self.strict else sympy.Ge
        result = op(self.lump, 0)
        result = sympy.simplify(result)
        return sympy.latex(result)

class Intersect(Boolean):
    def __and__(self, other):
        return self.add(other)
    @property
    def lump(self):
        return sympy.Min(*self.components)

class Union(Boolean):
    def __or__(self, other):
        return self.add(other)
    @property
    def lump(self):
        return sympy.Max(*self.components)

class XOR(Boolean):
    def __xor__(self, other):
        return self.add(other)
    @property
    def lump(self):
        return -sympy.Mul(*self.components)

html_fmt = lambda url,exp,opt,tree,config: """
<body style="background-color:#2A2A2A;" marginwidth="0px" marginheight="0px">
<style>
.dcg-smart-textarea-container {
    min-height: 24;
}
</style>
<script src="%(url)s"></script>
<div id="calculator"></div>
<script>
  var elt = document.getElementById("calculator");
  var calculator = Desmos.GraphingCalculator(elt, options=%(options)s);
  %(expressions)s

  state = calculator.getState();
  expr = state.expressions.list;
  folders = %(folders)s;
  for (folder in folders) {
    expr[folder].type = 'folder';
    expr[folder].title = expr[folder].text;
    expr[folder].collapsed = true;
    for (member of folders[folder]) {
      expr[member].folderId = expr[folder].id;
    }
  }
  calculator.setState(state);
  %(config)s
</script>
"""%{'url':url, 'expressions':exp, 'options':opt, 'folders':tree, 'config':config}

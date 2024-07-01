

from IPython.display import IFrame

import json
import sympy
import base64

class Calculator(object):
    def __init__(self, width=720, height=360, **kwargs):
        """
        Arguments:
            width - pixel width of iframe
            height - pixel height of iframe
            url - location of Desmos library
            url_fmt - location of Desmos library, parameterized with {"rev", "key"}
            key - Desmos key
            rev - Version of Desmos library
            **others - remaining kwargs are forwarded to Desmos as API options (see https://www.desmos.com/api/v1.9/docs/index.html)
        """
        self._width = width
        self._height = height

        kwargs,self._url = self.url_from_kwargs(**kwargs)

        # Overried default Desmos options, unless specified by user
        ## kwargs.setdefault('expressionsCollapsed', True)
        self._options = json.dumps(kwargs)

        self._cache = dict([(var,Statement(var)) for var in ('x','y','r','theta','pi','e')])
        self._statements = []
        self._substitutions = {}

    def url_from_kwargs(self, **kwargs):
        url = kwargs.pop('url', None)
        if not url:
            url_fmt = kwargs.pop('url_fmt', 'https://www.desmos.com/api/%(rev)s/calculator.js?apiKey=%(key)s')
            rev = kwargs.pop('rev', 'v1.9')
            key = kwargs.pop('key', 'dcb31709b452b1cf9dc26972add0fda6')
            url = url_fmt % {'rev': rev, 'key': key}
        return kwargs,url
    
    @property
    def html(self):
        expr = [latex_fmt(i, repr(str(e))) for i,e in enumerate(self._statements)]
        expr = '\n'.join(expr)
        for key,sub in self._substitutions.items():
            expr = expr.replace(key, sub)
        return html_fmt(self._url, expr, self._options)
    
    def save(self, filename):
        with open(filename, 'w') as f:
            f.write(self.html)
    
    def show(self, clear=True):
        data = base64.b64encode(self.html.encode('utf-8')).decode('utf-8')
        url = f'data:text/html;base64,{data}'
        display(IFrame(url, width=self._width, height=self._height))
        if clear:
            self._statements = []
            self._substitutions = {}

    def __getattr__(self, name):
        try:
            return self._cache[name]
        except:
            statement = Statement(name)
            self._cache[name] = statement
            return statement

    def __setattr__(self, name, value):
        if name[:1] == '_':
            return object.__setattr__(self, name, value)
        lhs = self.__getattr__(name)
        self.define(Equality(lhs, value))
    
    def define(self, expr):
        self._statements.append(expr)

    def abs(self, expr):
        val = Statement()
        val.sym = sympy.Abs(Statement.ref(expr))
        return val

    def point(self, *args):
        """
        Capture a point expression
            - sympy doesn't perform algebra (e.g. absolute value) on points -- it completely crashes
            - substitute a custom variable in the sympy expression, then replace this later with the latex string of the point
        """
        coords = [ sympy.latex(Statement.ref(expr)).replace('\\',r'\\') for expr in args ]
        coords = f'({", ".join(coords)})'
        var = 'v_{custom%04d}'%len(self._substitutions)
        self._substitutions[var] = coords
        return Statement(var)


class Statement(object):
    def __init__(self, value=None):
        if isinstance(value, str):
            self.name = value
            self.sym = sympy.symbols(value)

    @classmethod
    def from_value(cls, val):
        if isinstance(val, Statement):
            return val
        result = Statement()
        result.sym = val
        return result
    
    @staticmethod
    def ref(val):
        if isinstance(val, Statement):
            return val.sym
        return val
    
    def __eq__(self, other):
        return Equality(self.sym, Statement.ref(other))

    def __lt__(self, other):
        return LessThan(self.sym, Statement.ref(other))
    
    def __le__(self, other):
        return LessEqual(self.sym, Statement.ref(other))
    
    def __gt__(self, other):
        return GreaterThan(self.sym, Statement.ref(other))
    
    def __ge__(self, other):
        return GreaterEqual(self.sym, Statement.ref(other))
    
    def __req__(self, other):
        return Equality(Statement.ref(other), self.sym)

    def __add__(self, other):
        result = Statement()
        result.sym = self.sym + Statement.ref(other)
        return result

    def __radd__(self, other):
        result = Statement()
        result.sym = Statement.ref(other) + self.sym
        return result

    def __sub__(self, other):
        result = Statement()
        result.sym = self.sym - Statement.ref(other)
        return result

    def __rsub__(self, other):
        result = Statement()
        result.sym = Statement.ref(other) - self.sym
        return result

    def __mul__(self, other):
        result = Statement()
        result.sym = self.sym * Statement.ref(other)
        return result

    def __rmul__(self, other):
        result = Statement()
        result.sym = Statement.ref(other) * self.sym
        return result

    def __truediv__(self, other):
        result = Statement()
        result.sym = self.sym / Statement.ref(other)
        return result

    def __rtruediv__(self, other):
        result = Statement()
        result.sym = Statement.ref(other) / self.sym
        return result

    def __pow__(self, other):
        result = Statement()
        result.sym = self.sym ** Statement.ref(other)
        return result

    def __rpow__(self, other):
        result = Statement()
        result.sym = Statement.ref(other) ** self.sym
        return result

    def __str__(self):
        return sympy.latex(self.sym)

class Inequality(object):
    def __init__(self, lhs, rhs):
        if isinstance(lhs, Statement):
            lhs = lhs.sym
        if isinstance(rhs, Statement):
            rhs = rhs.sym
        self.lhs,self.rhs = (lhs, rhs)
        
    def __str__(self):
        return f'{sympy.latex(self.lhs)} {self.op} {sympy.latex(self.rhs)}'

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
        self.op = '\\lt'
        self.strict = True

    @property
    def lump(self):
        """ Returns an expression that is >= zero iff the original indequality is True. """
        return sympy.latex(self.rhs - self.lhs)

class LessEqual(Inequality):
    def __init__(self, lhs, rhs):
        super().__init__(lhs, rhs)
        self.op = '\\le'
        self.strict = False

    @property
    def lump(self):
        """ Returns an expression that is > zero iff the original indequality is True. """
        return sympy.latex(self.rhs - self.lhs)

class GreaterThan(Inequality):
    def __init__(self, lhs, rhs):
        super().__init__(lhs, rhs)
        self.op = '\\gt'
        self.strict = True

    @property
    def lump(self):
        """ Returns an expression that is > zero iff the original indequality is True. """
        return sympy.latex(self.lhs - self.rhs)

class GreaterEqual(Inequality):
    def __init__(self, lhs, rhs):
        super().__init__(lhs, rhs)
        self.op = '\\ge'
        self.strict = False

    @property
    def lump(self):
        """ Returns an expression that is >= zero iff the original indequality is True. """
        return sympy.latex(self.lhs - self.rhs)

class Equality(object):
    def __init__(self, lhs, rhs):
        if isinstance(lhs, Statement):
            lhs = lhs.sym
        if isinstance(rhs, Statement):
            rhs = rhs.sym
        self.sym = sympy.Eq(lhs, rhs)

    def __str__(self):
        return sympy.latex(self.sym)

class Boolean(object):
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
        else:
            self.components.append(component.lump)
        return self
    def __str__(self):
        op = '\\gt' if self.strict else '\\ge'
        return f'{self.lump} {op} 0'

class Intersect(Boolean):
    def __and__(self, other):
        return self.add(other)
    @property
    def lump(self):
        comps = ', '.join(str(c) for c in self.components)
        return f'min({comps})'

class Union(Boolean):
    def __or__(self, other):
        return self.add(other)
    @property
    def lump(self):
        comps = ', '.join(str(c) for c in self.components)
        return f'max({comps})'

class XOR(Boolean):
    def __xor__(self, other):
        return self.add(other)
    @property
    def lump(self):
        comps = '*'.join(f'({c})' for c in self.components)
        return f'-{comps}'

html_fmt = lambda url,exp,opt: """
<body style="background-color:#2A2A2A;" marginwidth="0px" marginheight="0px">
<script src="%(url)s"></script>
<div id="calculator"></div>
<script>
	var elt = document.getElementById("calculator");
	var calculator = Desmos.GraphingCalculator(elt, options=%(options)s);
	%(expressions)s
</script>
"""%{'url':url, 'expressions':exp, 'options':opt}

latex_fmt = lambda id,exp: """calculator.setExpression({
		latex: %(exp)s,
		id: '%(id)s',
	});
"""%{'exp':exp,'id':id}

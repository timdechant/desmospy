```python
!pip install 'desmospy>=0.0.5'
```

> [!NOTE]
>
> [Jump straight to the output *here*.](https://nbviewer.org/github/timdechant/desmospy/blob/main/examples/fourier-shapes/fourier-shapes.htm)
>
> [See a live view as a Jupyter notebook.](https://nbviewer.org/github/timdechant/desmospy/blob/main/examples/fourier-shapes/fourier-shapes.ipynb)
> 
> [See source code and more examples on github.](https://github.com/timdechant/desmospy)

# Python and Desmos

Python processing with Desmos interaction!  This shows the power of combining the two.

## Getting Started

Import the Calculator class from <code>desmospy</code> and create an instance.

<code>Calculator</code> takes one custom argument <code>size</code> to control the frame view; all other arguments are forwarded to the [Desmos API](https://www.desmos.com/api/v1.9/docs/index.html#document-calculator).


```python
from desmospy import Calculator
import numpy as np

calc = Calculator(size=(1200,600), showGrid=False, showXAxis=False, showYAxis=False)
```

Everything you need from desmospy is available using that <code>calc</code> object!

## Python Processing

We start by pulling in a CSV file containing a series of points.  This is then transformed into the frequency domain using a Fast Fourier Transform (FFT).


```python
j=(0+1j)

shape = np.loadtxt('shape.csv', skiprows=1, delimiter=",", dtype=float)
fft = np.fft.fft(shape[:,0] + j*shape[:,1])
fft = np.fft.fftshift(fft)

n = fft.shape[0]
mag = np.abs(fft/n)
phase = np.angle(fft)

fmax = n//2
freq = range(-fmax,fmax+1)

components = list(zip(freq,mag,phase))
components.sort(key=lambda fmp: abs(fmp[0]))
```

## Desmos Expressions

FFT converts the time-domain points (as a 2D sequence) into frequency components.

Each frequency component is define by three values: magnitude $m_i$, frequency $f_i$, and starting phase/angle $p_i$.

We will load these values into Desmos, then algebraically calculate the Inverse Fourier Transform:

$$
f(t) = \sum_{i=1}^{n} m_i \cdot \bigg(cos\big(2\pi \cdot t f_i + p_i\big) + j \cdot sin\big(2\pi \cdot t f_i + p_i\big)\bigg)
$$


```python
f_max = max(abs(f) for f,m,p in components if m > 0.08)

f_m_p = [ (f,round(m,2),round(p,2)) for f,m,p in components if m > 0.12]# if abs(f) <= f_max]
f,m,p = zip(*f_m_p)
# calc.n_f = len(f)

def subscript(f):
    sign_char = 'p' if f > 0 else 'n' if f < 0 else ''
    return sign_char + str(abs(f))

calc.f = f
calc.m = [ calc.__getattr__('m_{%s}'%subscript(f[i])) for i in range(len(m)) ]
calc.p = [ calc.__getattr__('p_{%s}'%subscript(f[i])) for i in range(len(p)) ]

folder = calc.folder('<== Open folder for components!')
for i in range(len(m)):
    folder.__setattr__('m_{%s}'%subscript(f[i]), m[i])
    folder.__getattr__('m_{%s}'%subscript(f[i])).config(sliderBounds={'min': 0, 'max': round(10*m[i],2)})
    folder.__setattr__('p_{%s}'%subscript(f[i]), p[i])
    folder.__getattr__('p_{%s}'%subscript(f[i])).config(sliderBounds={'min': round(-np.pi,2), 'max': round(np.pi,2)})

def unit_vector(theta):
    return calc.point(calc.cos(theta), calc.sin(theta))

@calc.function
def shape(t, n):
    def component(i):
        return calc.m[i-1] * unit_vector(2*calc.pi * t*calc.f[i-1] + calc.p[i-1])
    return calc.sum(component, i=[1,n])

calc.t_c = 0
calc.f_complete = shape(calc.range(1,3001)/3000, len(f))
calc.f_trace = shape(calc.t_c, calc.range(1,len(f)+1))
calc.f_dot = shape(calc.t_c, len(f))
```

Finally, we do a bit of formatting and display the results!


```python
calc.t_c.config(sliderBounds={'min': 0, 'max': 1}, playing=True) #, animationPeriod=80000, loopMode="LOOP_FORWARD")
calc.f_complete.config(points=False, lines=True, lineWidth=5, color="#87A5C4")
calc.f_trace.config(points=True, pointSize=3, lines=True, lineWidth=1, color="#111111")
calc.f_dot.config(pointSize=20, pointStyle="OPEN", color="black")

calc.bounds(left=-3, right=23, bottom=0, top=20)
calc.show(clear=False)
```
[<img src="fourier-shapes.gif">](https://nbviewer.org/github/timdechant/desmospy/blob/main/examples/fourier-shapes/fourier-shapes.htm)

We <code>show</code>'ed that with <code>clear=False</code>, so calc remains fully intact.  [Let's save a second copy to an HTML file; see it *here*.](https://nbviewer.org/github/timdechant/desmospy/blob/main/examples/fourier-shapes/fourier-shapes.htm).


```python
calc.save('fourier-shapes.htm')
```

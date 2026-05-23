"""
math_engine.py - J.A.R.V.I.S. Gelişmiş Matematik ve Analiz Motoru
Hesaplama, denklem çözme, istatistik, calculus ve daha fazlası.
"""

import math
import numpy as np
from typing import Union, List, Dict, Any, Optional
from decimal import Decimal, getcontext
import sympy as sp
from scipy import stats, optimize
import re

class MathEngine:
    """
    J.A.R.V.I.S.'in matematiksel işlemler için kullandığı gelişmiş motor.
    - Temel aritmetik
    - Denklem çözme
    - İstatistiksel analiz
    - Calculus (türev, integral)
    - Matris işlemleri
    - Birim dönüşümleri
    """
    
    def __init__(self):
        getcontext().prec = 50  # Yüksek hassasiyet
        self.operations_log = []
        
    def log(self, operation: str, result: Any):
        self.operations_log.append({
            "operation": operation,
            "result": str(result),
            "timestamp": __import__('time').time()
        })
        # Son 100 işlemi tut
        if len(self.operations_log) > 100:
            self.operations_log.pop(0)
    
    def evaluate_expression(self, expression: str) -> Dict[str, Any]:
        """
        Matematiksel ifadeyi değerlendirir.
        Örnek: "2 + 2 * 3", "sin(pi/2)", "sqrt(16)", "log10(100)"
        """
        try:
            # Güvenli değerlendirme için izin verilen fonksiyonlar
            safe_dict = {
                'abs': abs, 'round': round, 'min': min, 'max': max,
                'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
                'asin': math.asin, 'acos': math.acos, 'atan': math.atan,
                'sinh': math.sinh, 'cosh': math.cosh, 'tanh': math.tanh,
                'sqrt': math.sqrt, 'log': math.log, 'log10': math.log10,
                'log2': math.log2, 'exp': math.exp, 'pi': math.pi,
                'e': math.e, 'tau': math.tau, 'inf': float('inf'),
                'degrees': math.degrees, 'radians': math.radians,
                'floor': math.floor, 'ceil': math.ceil, 'factorial': math.factorial
            }
            result = eval(expression, {"__builtins__": {}}, safe_dict)
            self.log(f"eval: {expression}", result)
            return {
                "success": True,
                "expression": expression,
                "result": result,
                "type": type(result).__name__
            }
        except Exception as e:
            return {
                "success": False,
                "expression": expression,
                "error": str(e)
            }
    
    def solve_equation(self, equation: str, variable: str = 'x') -> Dict[str, Any]:
        """
        Denklem çözer.
        Örnek: "x**2 - 4 = 0" -> [-2, 2]
        """
        try:
            x = sp.Symbol(variable)
            # Denklemi düzenle
            if '=' in equation:
                left, right = equation.split('=')
                expr = sp.sympify(left) - sp.sympify(right)
            else:
                expr = sp.sympify(equation)
            
            solutions = sp.solve(expr, x)
            self.log(f"solve: {equation}", solutions)
            return {
                "success": True,
                "equation": equation,
                "variable": variable,
                "solutions": [float(s) if s.is_real else str(s) for s in solutions],
                "count": len(solutions)
            }
        except Exception as e:
            return {
                "success": False,
                "equation": equation,
                "error": str(e)
            }
    
    def derivative(self, expression: str, variable: str = 'x', order: int = 1) -> Dict[str, Any]:
        """
        Türev alır.
        Örnek: "x**2" -> "2*x"
        """
        try:
            x = sp.Symbol(variable)
            expr = sp.sympify(expression)
            deriv = sp.diff(expr, x, order)
            self.log(f"derivative: {expression}", deriv)
            return {
                "success": True,
                "expression": expression,
                "derivative": str(deriv),
                "order": order
            }
        except Exception as e:
            return {
                "success": False,
                "expression": expression,
                "error": str(e)
            }
    
    def integral(self, expression: str, variable: str = 'x', a: Optional[float] = None, b: Optional[float] = None) -> Dict[str, Any]:
        """
        İntegral alır (belirli veya belirsiz).
        """
        try:
            x = sp.Symbol(variable)
            expr = sp.sympify(expression)
            if a is not None and b is not None:
                result = sp.integrate(expr, (x, a, b))
                result_type = "definite"
            else:
                result = sp.integrate(expr, x)
                result_type = "indefinite"
            self.log(f"integral: {expression}", result)
            return {
                "success": True,
                "expression": expression,
                "integral": str(result),
                "type": result_type,
                "lower_bound": a,
                "upper_bound": b
            }
        except Exception as e:
            return {
                "success": False,
                "expression": expression,
                "error": str(e)
            }
    
    def statistics(self, data: List[float]) -> Dict[str, Any]:
        """
        İstatistiksel analiz yapar.
        """
        if not data:
            return {"success": False, "error": "Veri boş"}
        
        arr = np.array(data)
        return {
            "success": True,
            "count": len(data),
            "sum": float(np.sum(arr)),
            "mean": float(np.mean(arr)),
            "median": float(np.median(arr)),
            "mode": float(stats.mode(arr)[0]) if len(data) > 1 else data[0],
            "std": float(np.std(arr)),
            "variance": float(np.var(arr)),
            "min": float(np.min(arr)),
            "max": float(np.max(arr)),
            "range": float(np.max(arr) - np.min(arr)),
            "q1": float(np.percentile(arr, 25)),
            "q3": float(np.percentile(arr, 75)),
            "iqr": float(np.percentile(arr, 75) - np.percentile(arr, 25))
        }
    
    def matrix_operation(self, matrix_a: List[List[float]], operation: str, matrix_b: Optional[List[List[float]]] = None) -> Dict[str, Any]:
        """
        Matris işlemleri yapar.
        operation: "det", "inverse", "transpose", "add", "multiply"
        """
        try:
            A = np.array(matrix_a)
            
            if operation == "det":
                result = float(np.linalg.det(A))
            elif operation == "inverse":
                result = np.linalg.inv(A).tolist()
            elif operation == "transpose":
                result = A.T.tolist()
            elif operation == "add" and matrix_b:
                B = np.array(matrix_b)
                result = (A + B).tolist()
            elif operation == "multiply" and matrix_b:
                B = np.array(matrix_b)
                result = (A @ B).tolist()
            else:
                return {"success": False, "error": f"Geçersiz işlem: {operation}"}
            
            self.log(f"matrix: {operation}", result)
            return {
                "success": True,
                "operation": operation,
                "result": result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def convert_units(self, value: float, from_unit: str, to_unit: str) -> Dict[str, Any]:
        """
        Birim dönüşümü yapar.
        Desteklenen birimler: uzunluk, kütle, zaman, sıcaklık, vb.
        """
        conversions = {
            # Uzunluk
            'm': 1, 'km': 1000, 'cm': 0.01, 'mm': 0.001,
            'mile': 1609.34, 'yard': 0.9144, 'foot': 0.3048, 'inch': 0.0254,
            # Kütle
            'kg': 1, 'g': 0.001, 'mg': 0.000001, 'ton': 1000,
            'lb': 0.453592, 'oz': 0.0283495,
            # Zaman
            's': 1, 'min': 60, 'h': 3600, 'day': 86400,
            # Sıcaklık (özel işlem)
            'celsius': 'temp', 'fahrenheit': 'temp', 'kelvin': 'temp'
        }
        
        try:
            # Sıcaklık dönüşümleri
            if from_unit in ['celsius', 'fahrenheit', 'kelvin']:
                if from_unit == 'celsius' and to_unit == 'fahrenheit':
                    result = (value * 9/5) + 32
                elif from_unit == 'celsius' and to_unit == 'kelvin':
                    result = value + 273.15
                elif from_unit == 'fahrenheit' and to_unit == 'celsius':
                    result = (value - 32) * 5/9
                elif from_unit == 'fahrenheit' and to_unit == 'kelvin':
                    result = (value - 32) * 5/9 + 273.15
                elif from_unit == 'kelvin' and to_unit == 'celsius':
                    result = value - 273.15
                elif from_unit == 'kelvin' and to_unit == 'fahrenheit':
                    result = (value - 273.15) * 9/5 + 32
                else:
                    result = value
            else:
                # Standart dönüşüm
                if from_unit not in conversions or to_unit not in conversions:
                    return {"success": False, "error": f"Desteklenmeyen birim: {from_unit} -> {to_unit}"}
                result = value * (conversions[from_unit] / conversions[to_unit])
            
            self.log(f"convert: {value} {from_unit} -> {to_unit}", result)
            return {
                "success": True,
                "value": value,
                "from_unit": from_unit,
                "to_unit": to_unit,
                "result": result
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
from flask import Flask, render_template, request
import pandas as pd
import matplotlib
# Configuración IMPORTANTE para servidores (evita errores de pantalla)
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
import io
import base64
from scipy import optimize

# --- AQUÍ INICIAMOS LA APP WEB ---
app = Flask(__name__)

# --- TU LÓGICA MATEMÁTICA ---
def funcion_interes(i, v0, a, n, vf_deseado):
    if i == 0: 
        return (v0 + a * n) - vf_deseado
    monto_calculado = (v0 * (1 + i)**n) + (a * (((1 + i)**n - 1) / i))
    return monto_calculado - vf_deseado

# --- RUTA PRINCIPAL (LO QUE VE EL NAVEGADOR) ---
@app.route('/', methods=['GET', 'POST'])
def index():
    resultado = None
    tabla_html = None
    imagen_grafica = None
    error = None

    if request.method == 'POST':
        try:
            # 1. Obtener datos del formulario HTML
            v0 = float(request.form['v0'])
            a = float(request.form['aporte'])
            n = int(request.form['periodos'])
            vf = float(request.form['vf'])

            # 2. Calcular con Scipy
            # Buscamos tasa entre 0.0001% y 100%
            tasa = optimize.bisect(funcion_interes, 1e-6, 1.0, args=(v0, a, n, vf))
            tasa_porcentaje = round(tasa * 100, 4)

            # 3. Generar Tabla con Pandas
            lista_datos = []
            saldo = v0
            sin_int = v0
            for t in range(1, n + 1):
                interes = saldo * tasa
                saldo_fin = saldo + interes + a
                sin_int += a
                lista_datos.append({
                    'Periodo': t, 
                    'Saldo Inicial': saldo, 
                    'Interés': interes, 
                    'Aporte': a, 
                    'Saldo Final': saldo_fin
                })
                saldo = saldo_fin
            
            df = pd.DataFrame(lista_datos)
            
            # Convertir a HTML (usando clases de Bootstrap)
            tabla_html = df.to_html(classes='table table-striped table-hover', 
                                  float_format=lambda x: f"${x:,.2f}", index=False)

            # 4. Generar Gráfica
            plt.figure(figsize=(8, 4))
            plt.plot(df['Periodo'], df['Saldo Final'], label='Con Interés Compuesto', color='green')
            plt.plot(df['Periodo'], [sin_int/n * t + v0 for t in df['Periodo']], '--', label='Sin Interés', color='gray')
            plt.title(f'Proyección a {n} periodos')
            plt.xlabel('Periodo')
            plt.ylabel('Monto Acumulado ($)')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            # Guardar gráfica en memoria (para web)
            img = io.BytesIO()
            plt.savefig(img, format='png', bbox_inches='tight')
            img.seek(0)
            imagen_grafica = base64.b64encode(img.getvalue()).decode()
            plt.close()

            resultado = tasa_porcentaje

        except ValueError:
            error = "No es posible alcanzar esa meta con los valores dados (Intenta aumentar el tiempo o el aporte)."
        except Exception as e:
            error = f"Ocurrió un error inesperado: {e}"

    return render_template('index.html', 
                           tasa=resultado, 
                           tabla=tabla_html, 
                           grafica=imagen_grafica, 
                           error=error)

if __name__ == '__main__':
    app.run(debug=True)
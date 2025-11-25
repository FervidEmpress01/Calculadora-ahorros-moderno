from flask import Flask, render_template, request
import pandas as pd
import matplotlib
# Configuracion para servidores (evita errores de pantalla)
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
import io
import base64
from scipy import optimize

# Inicializar la aplicación Flask
app = Flask(__name__)

# Funcion para encontrar la tasa de interes
def funcion_interes(i, v0, a, n, vf_deseado):
    if i == 0: 
        # Si i es 0, es v0 + (n-1) aportes, porque el primero no se hace
        return (v0 + a * (n - 1)) - vf_deseado
    
    # El Valor Inicial crece por n periodos
    calculo_v0 = v0 * (1 + i)**n
    
    # Los aportes son una menos (n - 1) porque en la semana 1 no hubo aporte, por eso multiplicamos por (1+i) al final.
    periodos_aportes = n - 1
    if periodos_aportes > 0:
        parte_aportes = a * (((1 + i)**periodos_aportes - 1) / i) * (1 + i)
    else:
        parte_aportes = 0
    
    monto_calculado = calculo_v0 + parte_aportes
    return monto_calculado - vf_deseado

@app.route('/', methods=['GET', 'POST'])
def index():
    resultado = None
    tabla_html = None
    imagen_grafica = None
    error = None
    freq_nombre = "Periódica" 

    if request.method == 'POST':
        try:
            v0 = float(request.form['v0'])
            a = float(request.form['aporte'])
            n = int(request.form['periodos'])
            vf = float(request.form['vf'])
            
            # Capturamos la frecuencia del formulario
            freq_nombre = request.form.get('frecuencia', 'Periódica')

            # Restricciones de entrada
            if v0 < 50:
                    error = "El depósito inicial debe ser de al menos $50."
            elif a < 5:
                    error = "El aporte periódico debe ser de al menos $5."
            elif vf <= v0:
                    error = "La meta debe ser mayor al depósito inicial."
            elif n <= 0:
                    error = "El número de periodos debe ser mayor a cero."
            else:
                # Buscamos tasa entre 0.000001% y 100% con metodo de bisección
                tasa = optimize.bisect(funcion_interes, 1e-6, 1, args=(v0, a, n, vf))
                tasa_porcentaje = round(tasa * 100, 4)

                # Generar Tabla de Amortización
                lista_datos = []
                saldo = v0
                sin_int = v0
                
                for t in range(1, n + 1):
                    # CORRECCIÓN: Semana 1 aporte es 0, Semana 2 en adelante es 'a'
                    if t == 1:
                        aporte_real = 0
                    else:
                        aporte_real = a

                    # Calculamos interés sobre la base (Saldo + Aporte actual)
                    base_calculo = saldo + aporte_real
                    interes = base_calculo * tasa
                    saldo_fin = base_calculo + interes
                    
                    sin_int += aporte_real

                    lista_datos.append({
                        'Periodo': t, 
                        'Saldo Inicial': saldo, 
                        # Mostramos 0 en la semana 1 visualmente, a partir de la 2 mostramos 'a'
                        'Aporte': a if t > 1 else 0, 
                        'Interés': interes, 
                        'Saldo Final': saldo_fin
                    })
                    saldo = saldo_fin
                
                df = pd.DataFrame(lista_datos)
                
                tabla_html = df.to_html(classes='table table-striped table-hover', 
                                      float_format=lambda x: f"${x:,.2f}", index=False)

                # 4. Generar Gráfica
                plt.figure(figsize=(8, 4))
                plt.plot(df['Periodo'], df['Saldo Final'], label='Con Interés Compuesto', color='green')
                # Ajustamos la linea gris para que cuadre con la logica n-1
                plt.plot(df['Periodo'], [v0 + (a * (t-1) if t>0 else 0) for t in df['Periodo']], '--', label='Sin Interés', color='gray')
                
                # Título dinámico con la frecuencia
                plt.title(f'Proyección {freq_nombre} a {n} periodos')
                plt.xlabel(f'Periodo ({freq_nombre})')
                plt.ylabel('Monto Acumulado ($)')
                plt.legend()
                plt.grid(True, alpha=0.3)
                
                # Guardar gráfica en memoria (para mostrar en render)
                img = io.BytesIO() # Objeto en memoria
                plt.savefig(img, format='png', bbox_inches='tight') # Guardar figura en objeto
                img.seek(0)
                imagen_grafica = base64.b64encode(img.getvalue()).decode() # Codificar a base64 para HTML
                plt.close()

                resultado = tasa_porcentaje

        except ValueError:
            error = "No es posible alcanzar esa meta con los valores dados (Intenta aumentar el tiempo o el aporte)."
        except Exception as e:
            error = f"Ocurrió un error inesperado: {e}"

    # Pasamos freq_nombre al template
    return render_template('index.html', 
                           tasa=resultado,
                           frecuencia_nombre=freq_nombre,
                           tabla=tabla_html, 
                           grafica=imagen_grafica, 
                           error=error)

if __name__ == '__main__':
    app.run(debug=True)
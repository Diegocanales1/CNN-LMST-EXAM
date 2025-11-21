import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def obtener_datos_polipropileno():
    """
    Abre el navegador, extrae datos de la gráfica de TradingEconomics 
    y devuelve un DataFrame limpio y ordenado.
    """
    
    # CONFIGURACIÓN DEL NAVEGADOR
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(options=options)

    datos_extraidos = []
    url = "https://tradingeconomics.com/commodity/polypropylene"

    try:
        print("🚀 Iniciando scraper...")
        driver.get(url)
        driver.maximize_window()
        
        # Scroll y espera para asegurar carga de la gráfica (Highcharts)
        driver.execute_script("window.scrollBy(0, 400);")
        time.sleep(5) 

        print("🔍 Localizando gráfica...")
        chart_element = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "highcharts-container"))
        )
        
        width = chart_element.size['width']
        print(f"✅ Gráfica detectada ({width}px). Escaneando...")

        action = ActionChains(driver)
        start_x = - (width / 2)
        step = 2
        
        # BUCLE DE EXTRACCIÓN
        for offset in range(0, width, step):
            current_x = start_x + offset
            
            try:
                # Mover el mouse
                action.move_to_element(chart_element).move_by_offset(current_x, 0).perform()
                
                fecha_txt = None
                precio_txt = None

                # Capturar FECHA (Etiqueta flotante abajo: yLabelDrag)
                try:
                    elementos_fecha = driver.find_elements(By.CLASS_NAME, "yLabelDrag")
                    for el in elementos_fecha:
                        txt = el.get_attribute("textContent").strip()
                        if txt and any(c.isalpha() for c in txt): 
                            fecha_txt = txt
                            break
                except:
                    pass

                # Capturar PRECIO (Encabezado fijo arriba: closeLabel)
                try:
                    elemento_precio = driver.find_element(By.CLASS_NAME, "closeLabel")
                    precio_txt = elemento_precio.text.strip()
                except:
                    pass

                # Solo agregamos si tenemos el par completo
                if fecha_txt and precio_txt:
                    datos_extraidos.append({
                        "Fecha": fecha_txt,
                        "Precio": precio_txt
                    })

            except Exception:
                pass # Ignorar errores puntuales al mover el mouse

    finally:
        print("🔒 Cerrando navegador...")
        driver.quit()

    # LIMPIEZA Y PROCESAMIENTO
    print("🧹 Procesando y limpiando datos...")
    
    if not datos_extraidos:
        print("❌ No se extrajeron datos.")
        return None

    df = pd.DataFrame(datos_extraidos)

    # Limpieza de duplicados crudos (por si el mouse se detuvo mucho tiempo)
    df = df.drop_duplicates()

    # Convertir Fecha de texto a Objeto Datetime real
    df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
    
    # Convertir Precio a Float (quitando comas si existen)
    df['Precio'] = df['Precio'].astype(str).str.replace(',', '').astype(float)

    # Eliminación de valores nulos (si falló la conversión)
    df = df.dropna()

    # ORDENAMIENTO CRONOLÓGICO (Vital para Series de Tiempo)
    df = df.sort_values(by='Fecha', ascending=True)

    # Resetear índice y quitar duplicados de fechas (quedarse con el último valor registrado del día)
    df = df.drop_duplicates(subset=['Fecha'], keep='last')
    df = df.reset_index(drop=True)

    return df

# EJECUCIÓN PRINCIPAL
if __name__ == "__main__":
    df_final = obtener_datos_polipropileno()
    
    if df_final is not None:
        nombre_archivo = "dataset_polipropileno.csv"
        df_final.to_csv(nombre_archivo, index=False)
        
        print("\n" + "="*40)
        print(f"🏆 ¡ÉXITO! Dataset generado correctamente.")
        print(f"📅 Rango de fechas: {df_final['Fecha'].min().date()} a {df_final['Fecha'].max().date()}")
        print(f"📊 Total registros: {len(df_final)}")
        print(f"💾 Guardado en: {nombre_archivo}")
        print("="*40)
        print(df_final.head())
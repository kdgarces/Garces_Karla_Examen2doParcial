# Inventario de restaurante — Segundo parcial

## Descripción

Aplicación de escritorio desarrollada en Python para administrar el inventario de un restaurante de comida rápida. Los productos se clasifican en **Congelados**, **Refrigerados** y **Secos**.

El sistema cuenta con una interfaz gráfica creada con Flet y permite agregar, buscar, actualizar, eliminar, filtrar y consultar productos. También identifica existencias bajas, calcula el valor total del inventario y permite restaurar productos eliminados.

La información se almacena de forma persistente en el archivo `inventario.json`. Esto permite cerrar la aplicación y recuperar tanto los productos activos como la pila de productos eliminados al ejecutarla nuevamente.

## Objetivo del proyecto

Desarrollar una aplicación de inventario funcional que integre una interfaz gráfica, validación de datos, operaciones CRUD y almacenamiento persistente. El sistema también aplica una pila manual con comportamiento LIFO, el patrón Repository y pruebas unitarias para separar responsabilidades y comprobar su funcionamiento.

## Principales funcionalidades

- Registrar y validar productos con Pydantic.
- Crear, consultar, actualizar y eliminar productos.
- Clasificar productos en Congelados, Refrigerados y Secos.
- Filtrar productos por categoría o por stock bajo.
- Calcular la cantidad de productos y el valor total del inventario.
- Mostrar visualmente los productos disponibles y con stock bajo.
- Guardar automáticamente los cambios en `inventario.json`.
- Recuperar los datos guardados al iniciar la aplicación.
- Conservar la pila de productos eliminados después de cerrar el programa.
- Restaurar el último producto eliminado según el principio LIFO.
- Evitar códigos duplicados y operaciones inválidas.
- Ejecutar pruebas unitarias automatizadas con pytest.

## Persistencia de datos

La clase `RepositorioArchivoJSON` administra el almacenamiento permanente. El archivo contiene dos colecciones:

```json
{
  "productos": [],
  "productos_eliminados": []
}
```

La primera colección conserva los productos activos. La segunda conserva los productos eliminados desde la base hasta el tope de la pila. Cada operación que modifica el inventario actualiza el archivo automáticamente.

Para demostrar la persistencia se puede registrar un producto, cerrar la aplicación y ejecutarla nuevamente. El producto aparecerá otra vez porque se recupera desde el archivo JSON.

## Interfaz gráfica

La interfaz fue desarrollada con Flet. Incluye:

- Formulario para ingresar los datos del producto.
- Botones para agregar, buscar, actualizar, eliminar y limpiar.
- Opciones para consultar y restaurar el último producto eliminado.
- Filtro por categoría y por stock bajo.
- Tabla de productos registrados.
- Resumen de productos, stock bajo y valor total.
- Mensajes de confirmación y error.
- Indicador del archivo utilizado para la persistencia.

## Pila manual

`PilaProductosEliminados` utiliza una lista de capacidad fija y un contador interno:

```python
self._elementos = [None] * capacidad
self._cantidad = 0
```

La pila implementa manualmente:

- `apilar()`: agrega un producto al tope.
- `desapilar()`: retira el producto del tope.
- `ver_tope()`: consulta el siguiente producto sin retirarlo.
- `esta_vacia()`: comprueba si no existen elementos.
- `esta_llena()`: comprueba si se alcanzó la capacidad.
- `listar()`: devuelve una copia ordenada para guardar la pila en JSON.

La estructura aplica el principio **LIFO**: el último producto eliminado es el primero que puede restaurarse.

## Patrón Repository

El sistema utiliza diferentes repositorios para separar el almacenamiento de la lógica y de la interfaz:

- `RepositorioProductos`: administra los productos activos y las operaciones CRUD.
- `RepositorioProductosEliminados`: encapsula la pila manual.
- `RepositorioArchivoJSON`: guarda y recupera el estado persistente.
- `InventarioRestaurante`: coordina los repositorios y las reglas del sistema.

La comunicación principal es:

```text
Interfaz Flet → InventarioRestaurante → Repositories → JSON y pila manual
```

## Estructura del repositorio

```text
Garces_Karla_ExamenSegundoParcial.py   Código principal e interfaz gráfica
test_examen_segundo_parcial.py         Pruebas unitarias
inventario.json                        Almacenamiento persistente
requirements.txt                       Dependencias del proyecto
README.md                              Documentación
.gitignore                             Archivos excluidos de Git
```

## Requisitos

- Python 3.10 o una versión posterior.
- Flet.
- Pydantic 2.
- pytest 8.

## Instalación

1. Descargar o clonar el repositorio.
2. Abrir una terminal dentro de la carpeta del proyecto.
3. Instalar las dependencias:

```bash
python -m pip install -r requirements.txt
```

## Ejecutar la aplicación

```bash
python Garces_Karla_ExamenSegundoParcial.py
```

Se puede seleccionar **Cargar datos de prueba** para registrar quince productos de ejemplo. Los productos quedarán guardados en `inventario.json`.

## Ejecutar las pruebas unitarias

```bash
python -m pytest -v
```

Las pruebas comprueban la pila, los casos límite, las operaciones CRUD, el patrón Repository, la eliminación y restauración, el filtro de stock bajo y la persistencia de datos después de reiniciar el inventario.

## Lenguaje y tecnologías

- Python
- Flet
- Pydantic
- pytest
- JSON

## Estudiante

**Karla D. Garcés**

Proyecto académico desarrollado para la asignatura **Programación Estructurada**.

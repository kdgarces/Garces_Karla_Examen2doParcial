import json
from pathlib import Path
from typing import Literal

import flet as ft
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator


Categoria = Literal["Congelados", "Refrigerados", "Secos"]


class Producto(BaseModel):
    """Representa un producto almacenado en el restaurante."""

    model_config = ConfigDict(
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    codigo: str = Field(min_length=3, max_length=12)
    nombre: str = Field(min_length=2, max_length=60)
    categoria: Categoria
    cantidad: float = Field(ge=0)
    unidad: str = Field(min_length=1, max_length=20)
    costo_unitario: float = Field(gt=0)
    stock_minimo: float = Field(ge=0)

    @field_validator("codigo")
    @classmethod
    def validar_codigo(cls, codigo: str) -> str:
        codigo = codigo.upper()
        if not codigo.isalnum():
            raise ValueError("El código solo debe contener letras y números.")
        return codigo

    @field_validator("nombre", "unidad")
    @classmethod
    def validar_texto(cls, texto: str) -> str:
        if not any(caracter.isalpha() for caracter in texto):
            raise ValueError("El campo debe contener letras.")
        return texto.title()

    @property
    def valor_total(self) -> float:
        return self.cantidad * self.costo_unitario

    @property
    def tiene_stock_bajo(self) -> bool:
        return self.cantidad <= self.stock_minimo


class PilaProductosEliminados:
    """Pila LIFO manual implementada sobre un arreglo de capacidad fija."""

    def __init__(self, capacidad: int) -> None:
        if capacidad <= 0:
            raise ValueError("La capacidad debe ser mayor que cero.")

        # La lista simula un arreglo de tamaño fijo, como se explicó en clase.
        self._elementos: list[Producto | None] = [None] * capacidad
        self._cantidad = 0

    def apilar(self, producto: Producto) -> None:
        if self.esta_llena():
            raise IndexError("La pila de productos eliminados está llena.")

        self._elementos[self._cantidad] = producto
        self._cantidad += 1

    def desapilar(self) -> Producto:
        if self.esta_vacia():
            raise IndexError("No hay productos eliminados para restaurar.")

        self._cantidad -= 1
        producto = self._elementos[self._cantidad]
        self._elementos[self._cantidad] = None

        # La posición ocupada siempre contiene un Producto. La comprobación
        # mantiene el tipo de retorno explícito sin exponer el arreglo interno.
        if producto is None:
            raise RuntimeError("La pila contiene un estado inválido.")
        return producto

    def ver_tope(self) -> Producto:
        if self.esta_vacia():
            raise IndexError("No hay productos eliminados para consultar.")

        producto = self._elementos[self._cantidad - 1]
        if producto is None:
            raise RuntimeError("La pila contiene un estado inválido.")
        return producto

    def esta_vacia(self) -> bool:
        return self._cantidad == 0

    def esta_llena(self) -> bool:
        return self._cantidad == len(self._elementos)

    def get_cantidad(self) -> int:
        return self._cantidad

    def get_capacidad(self) -> int:
        return len(self._elementos)

    def listar(self) -> list[Producto]:
        """Devuelve una copia desde la base hasta el tope de la pila."""
        return [
            producto
            for producto in self._elementos[: self._cantidad]
            if producto is not None
        ]


class RepositorioProductos:
    """Centraliza el almacenamiento y las operaciones CRUD de productos."""

    def __init__(self) -> None:
        self._productos: list[Producto] = []
        self._productos_por_codigo: dict[str, Producto] = {}
        self._codigos_registrados: set[str] = set()

    @staticmethod
    def preparar_codigo(codigo: str) -> str:
        return codigo.strip().upper()

    def agregar(self, producto: Producto) -> None:
        codigo = self.preparar_codigo(producto.codigo)
        if codigo in self._codigos_registrados:
            raise ValueError(f"Ya existe un producto con el código {codigo}.")

        self._productos.append(producto)
        self._productos_por_codigo[codigo] = producto
        self._codigos_registrados.add(codigo)

    def obtener(self, codigo: str) -> Producto:
        codigo = self.preparar_codigo(codigo)
        if codigo not in self._productos_por_codigo:
            raise KeyError(f"No existe un producto con el código {codigo}.")
        return self._productos_por_codigo[codigo]

    def existe(self, codigo: str) -> bool:
        return self.preparar_codigo(codigo) in self._codigos_registrados

    def listar(self) -> list[Producto]:
        # Devuelve una copia para no exponer la colección interna.
        return list(self._productos)

    def actualizar(
        self,
        codigo: str,
        nombre: str,
        categoria: Categoria,
        cantidad: float,
        unidad: str,
        costo_unitario: float,
        stock_minimo: float,
    ) -> Producto:
        producto = self.obtener(codigo)

        datos_validados = Producto(
            codigo=producto.codigo,
            nombre=nombre,
            categoria=categoria,
            cantidad=cantidad,
            unidad=unidad,
            costo_unitario=costo_unitario,
            stock_minimo=stock_minimo,
        )

        producto.nombre = datos_validados.nombre
        producto.categoria = datos_validados.categoria
        producto.cantidad = datos_validados.cantidad
        producto.unidad = datos_validados.unidad
        producto.costo_unitario = datos_validados.costo_unitario
        producto.stock_minimo = datos_validados.stock_minimo
        return producto

    def eliminar(self, codigo: str) -> Producto:
        producto = self.obtener(codigo)
        self._productos.remove(producto)
        del self._productos_por_codigo[producto.codigo]
        self._codigos_registrados.remove(producto.codigo)
        return producto

    def cantidad(self) -> int:
        return len(self._productos)


class RepositorioProductosEliminados:
    """Aplica Repository sobre la pila manual de productos eliminados."""

    def __init__(self, capacidad: int = 50) -> None:
        self._pila = PilaProductosEliminados(capacidad)

    def guardar(self, producto: Producto) -> None:
        self._pila.apilar(producto)

    def retirar_ultimo(self) -> Producto:
        return self._pila.desapilar()

    def consultar_ultimo(self) -> Producto:
        return self._pila.ver_tope()

    def esta_vacio(self) -> bool:
        return self._pila.esta_vacia()

    def esta_lleno(self) -> bool:
        return self._pila.esta_llena()

    def cantidad(self) -> int:
        return self._pila.get_cantidad()

    def capacidad(self) -> int:
        return self._pila.get_capacidad()

    def listar(self) -> list[Producto]:
        return self._pila.listar()


class RepositorioArchivoJSON:
    """Guarda y recupera el estado completo del inventario en formato JSON."""

    def __init__(self, ruta: str | Path) -> None:
        self._ruta = Path(ruta)

    @property
    def ruta(self) -> Path:
        return self._ruta

    def cargar(self) -> tuple[list[Producto], list[Producto]]:
        if not self._ruta.exists():
            return [], []

        contenido = self._ruta.read_text(encoding="utf-8").strip()
        if not contenido:
            return [], []

        try:
            datos = json.loads(contenido)
        except json.JSONDecodeError as error:
            raise ValueError(
                f"El archivo {self._ruta.name} no contiene un JSON válido."
            ) from error

        if not isinstance(datos, dict):
            raise ValueError("El archivo del inventario debe contener un objeto JSON.")

        productos_datos = datos.get("productos", [])
        eliminados_datos = datos.get("productos_eliminados", [])
        if not isinstance(productos_datos, list) or not isinstance(
            eliminados_datos, list
        ):
            raise ValueError(
                "Las colecciones productos y productos_eliminados deben ser listas."
            )

        productos = [Producto.model_validate(item) for item in productos_datos]
        eliminados = [Producto.model_validate(item) for item in eliminados_datos]
        return productos, eliminados

    def guardar(
        self,
        productos: list[Producto],
        productos_eliminados: list[Producto],
    ) -> None:
        datos = {
            "productos": [producto.model_dump(mode="json") for producto in productos],
            "productos_eliminados": [
                producto.model_dump(mode="json")
                for producto in productos_eliminados
            ],
        }

        self._ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta_temporal = self._ruta.with_suffix(self._ruta.suffix + ".tmp")
        ruta_temporal.write_text(
            json.dumps(datos, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        ruta_temporal.replace(self._ruta)


class InventarioRestaurante:
    """Contiene la lógica del inventario y coordina sus repositorios."""

    def __init__(
        self,
        repositorio: RepositorioProductos | None = None,
        repositorio_eliminados: RepositorioProductosEliminados | None = None,
        persistencia: RepositorioArchivoJSON | None = None,
    ) -> None:
        self._repositorio = repositorio or RepositorioProductos()
        self._repositorio_eliminados = (
            repositorio_eliminados or RepositorioProductosEliminados()
        )
        self._persistencia = persistencia

        if self._persistencia is not None:
            productos, eliminados = self._persistencia.cargar()
            for producto in productos:
                self._repositorio.agregar(producto)
            for producto in eliminados:
                self._repositorio_eliminados.guardar(producto)

    def _guardar_estado(self) -> None:
        if self._persistencia is not None:
            self._persistencia.guardar(
                self._repositorio.listar(),
                self._repositorio_eliminados.listar(),
            )

    def agregar_producto(self, producto: Producto) -> None:
        self._repositorio.agregar(producto)
        try:
            self._guardar_estado()
        except Exception:
            self._repositorio.eliminar(producto.codigo)
            raise

    def buscar_producto(self, codigo: str) -> Producto:
        return self._repositorio.obtener(codigo)

    def existe_producto(self, codigo: str) -> bool:
        return self._repositorio.existe(codigo)

    def listar_productos(self, categoria: str = "Todos") -> list[Producto]:
        productos = self._repositorio.listar()
        if categoria == "Todos":
            return productos
        if categoria == "Stock bajo":
            return [producto for producto in productos if producto.tiene_stock_bajo]
        return [producto for producto in productos if producto.categoria == categoria]

    def actualizar_producto(
        self,
        codigo: str,
        nombre: str,
        categoria: Categoria,
        cantidad: float,
        unidad: str,
        costo_unitario: float,
        stock_minimo: float,
    ) -> Producto:
        anterior = self._repositorio.obtener(codigo).model_copy(deep=True)
        actualizado = self._repositorio.actualizar(
            codigo,
            nombre,
            categoria,
            cantidad,
            unidad,
            costo_unitario,
            stock_minimo,
        )
        try:
            self._guardar_estado()
        except Exception:
            self._repositorio.actualizar(
                anterior.codigo,
                anterior.nombre,
                anterior.categoria,
                anterior.cantidad,
                anterior.unidad,
                anterior.costo_unitario,
                anterior.stock_minimo,
            )
            raise
        return actualizado

    def eliminar_producto(self, codigo: str) -> Producto:
        if self._repositorio_eliminados.esta_lleno():
            raise IndexError("No se puede eliminar: la pila de eliminados está llena.")

        producto = self._repositorio.eliminar(codigo)
        guardado_en_pila = False
        try:
            self._repositorio_eliminados.guardar(producto)
            guardado_en_pila = True
            self._guardar_estado()
        except Exception:
            if guardado_en_pila:
                self._repositorio_eliminados.retirar_ultimo()
            self._repositorio.agregar(producto)
            raise
        return producto

    def consultar_ultimo_eliminado(self) -> Producto:
        return self._repositorio_eliminados.consultar_ultimo()

    def restaurar_ultimo_eliminado(self) -> Producto:
        producto = self._repositorio_eliminados.retirar_ultimo()
        agregado_al_inventario = False
        try:
            self._repositorio.agregar(producto)
            agregado_al_inventario = True
            self._guardar_estado()
        except Exception:
            if agregado_al_inventario:
                self._repositorio.eliminar(producto.codigo)
            self._repositorio_eliminados.guardar(producto)
            raise
        return producto

    def cantidad_productos(self) -> int:
        return self._repositorio.cantidad()

    def cantidad_eliminados(self) -> int:
        return self._repositorio_eliminados.cantidad()

    def valor_total_inventario(self) -> float:
        return sum(producto.valor_total for producto in self._repositorio.listar())

    def cantidad_stock_bajo(self) -> int:
        return sum(
            producto.tiene_stock_bajo for producto in self._repositorio.listar()
        )


DATOS_PRUEBA = [
    ("CON001", "Chicken tenders", "Congelados", 8, "Cajas", 32.50, 5),
    ("CON002", "Pescado", "Congelados", 4, "Cajas", 48.00, 5),
    ("CON003", "Camarones", "Congelados", 6, "Bolsas", 38.75, 4),
    ("CON004", "Papas fritas", "Congelados", 12, "Cajas", 29.90, 6),
    ("CON005", "Onion rings", "Congelados", 3, "Cajas", 26.50, 4),
    ("REF001", "Carne molida", "Refrigerados", 25, "Libras", 4.80, 10),
    ("REF002", "Huevos", "Refrigerados", 90, "Unidades", 0.32, 30),
    ("REF003", "Lechuga", "Refrigerados", 14, "Unidades", 1.75, 8),
    ("REF004", "Queso", "Refrigerados", 18, "Libras", 5.60, 8),
    ("REF005", "Bacon", "Refrigerados", 9, "Libras", 6.90, 5),
    ("SEC001", "Sal", "Secos", 10, "Bolsas", 3.25, 3),
    ("SEC002", "Pimienta", "Secos", 6, "Frascos", 5.40, 2),
    ("SEC003", "Azúcar", "Secos", 20, "Libras", 1.20, 8),
    ("SEC004", "Kétchup", "Secos", 7, "Cajas", 24.50, 4),
    ("SEC005", "Sirope para soda", "Secos", 2, "Cajas", 79.00, 3),
]


def mensaje_error_pydantic(error: ValidationError) -> str:
    primer_error = error.errors()[0]
    campo = str(primer_error["loc"][0]).replace("_", " ").capitalize()
    mensaje = primer_error["msg"].replace("Value error, ", "")
    return f"{campo}: {mensaje}"


def main(page: ft.Page) -> None:
    page.title = "Inventario de restaurante"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 24
    page.scroll = ft.ScrollMode.AUTO

    ruta_datos = Path(__file__).with_name("inventario.json")
    inventario = InventarioRestaurante(
        persistencia=RepositorioArchivoJSON(ruta_datos)
    )

    codigo = ft.TextField(label="Código", hint_text="Ejemplo: CON001")
    nombre = ft.TextField(label="Nombre del producto")
    categoria = ft.Dropdown(
        label="Categoría",
        value="Congelados",
        options=[
            ft.DropdownOption(key="Congelados", text="Congelados"),
            ft.DropdownOption(key="Refrigerados", text="Refrigerados"),
            ft.DropdownOption(key="Secos", text="Secos"),
        ],
    )
    cantidad = ft.TextField(label="Cantidad", keyboard_type=ft.KeyboardType.NUMBER)
    unidad = ft.Dropdown(
        label="Unidad",
        value="Unidades",
        options=[
            ft.DropdownOption(key=valor, text=valor)
            for valor in (
                "Unidades",
                "Libras",
                "Kilogramos",
                "Bolsas",
                "Cajas",
                "Galones",
                "Botellas",
                "Frascos",
            )
        ],
    )
    costo = ft.TextField(
        label="Costo unitario ($)", keyboard_type=ft.KeyboardType.NUMBER
    )
    stock_minimo = ft.TextField(
        label="Stock mínimo", keyboard_type=ft.KeyboardType.NUMBER
    )

    filtro = ft.Dropdown(
        label="Filtrar productos",
        value="Todos",
        width=230,
        options=[
            ft.DropdownOption(key=valor, text=valor)
            for valor in (
                "Todos",
                "Congelados",
                "Refrigerados",
                "Secos",
                "Stock bajo",
            )
        ],
    )

    productos_recuperados = inventario.cantidad_productos()
    mensaje_inicial = (
        f"Se recuperaron {productos_recuperados} productos desde {ruta_datos.name}."
        if productos_recuperados
        else "No hay productos guardados. Complete el formulario para comenzar."
    )
    mensaje = ft.Text(mensaje_inicial, color=ft.Colors.BLUE_700)
    estado_persistencia = ft.Text(
        f"Persistencia activa: {ruta_datos.name}",
        color=ft.Colors.BLUE_700,
    )
    resumen = ft.Text(weight=ft.FontWeight.BOLD)
    estado_pila = ft.Text(color=ft.Colors.DEEP_ORANGE_700)
    tabla = ft.DataTable(
        columns=[
            ft.DataColumn(label=ft.Text("Código")),
            ft.DataColumn(label=ft.Text("Producto")),
            ft.DataColumn(label=ft.Text("Categoría")),
            ft.DataColumn(label=ft.Text("Cantidad")),
            ft.DataColumn(label=ft.Text("Unidad")),
            ft.DataColumn(label=ft.Text("Costo")),
            ft.DataColumn(label=ft.Text("Estado")),
        ],
        rows=[],
        border=ft.Border.all(1, ft.Colors.GREY_300),
        heading_row_color=ft.Colors.BLUE_GREY_50,
    )

    def mostrar_mensaje(texto: str, es_error: bool = False) -> None:
        mensaje.value = texto
        mensaje.color = ft.Colors.RED_700 if es_error else ft.Colors.GREEN_700

    def convertir_numero(valor: str | None, nombre_campo: str) -> float:
        try:
            return float((valor or "").strip().replace(",", "."))
        except ValueError:
            raise ValueError(f"{nombre_campo} debe ser un número válido.")

    def crear_desde_formulario() -> Producto:
        return Producto(
            codigo=codigo.value or "",
            nombre=nombre.value or "",
            categoria=categoria.value,
            cantidad=convertir_numero(cantidad.value, "La cantidad"),
            unidad=unidad.value,
            costo_unitario=convertir_numero(costo.value, "El costo unitario"),
            stock_minimo=convertir_numero(stock_minimo.value, "El stock mínimo"),
        )

    def limpiar_formulario(evento=None) -> None:
        codigo.value = ""
        codigo.disabled = False
        nombre.value = ""
        categoria.value = "Congelados"
        cantidad.value = ""
        unidad.value = "Unidades"
        costo.value = ""
        stock_minimo.value = ""
        if evento is not None:
            mostrar_mensaje("Formulario limpio.")
            page.update()

    def cargar_en_formulario(producto: Producto) -> None:
        codigo.value = producto.codigo
        codigo.disabled = True
        nombre.value = producto.nombre
        categoria.value = producto.categoria
        cantidad.value = f"{producto.cantidad:g}"
        unidad.value = producto.unidad
        costo.value = f"{producto.costo_unitario:.2f}"
        stock_minimo.value = f"{producto.stock_minimo:g}"

    def actualizar_resumen_pila() -> None:
        cantidad_guardada = inventario.cantidad_eliminados()
        if cantidad_guardada == 0:
            estado_pila.value = "Pila de eliminados: vacía"
        else:
            ultimo = inventario.consultar_ultimo_eliminado()
            estado_pila.value = (
                f"Pila de eliminados: {cantidad_guardada} | "
                f"Tope: {ultimo.codigo} - {ultimo.nombre}"
            )

    def actualizar_tabla() -> None:
        tabla.rows.clear()
        for producto in inventario.listar_productos(filtro.value or "Todos"):
            estado = "Stock bajo" if producto.tiene_stock_bajo else "Disponible"
            color_estado = (
                ft.Colors.RED_700
                if producto.tiene_stock_bajo
                else ft.Colors.GREEN_700
            )
            tabla.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(producto.codigo)),
                        ft.DataCell(ft.Text(producto.nombre)),
                        ft.DataCell(ft.Text(producto.categoria)),
                        ft.DataCell(ft.Text(f"{producto.cantidad:g}")),
                        ft.DataCell(ft.Text(producto.unidad)),
                        ft.DataCell(ft.Text(f"${producto.costo_unitario:.2f}")),
                        ft.DataCell(ft.Text(estado, color=color_estado)),
                    ],
                    on_select_change=lambda evento, p=producto: cargar_y_actualizar(p),
                )
            )

        resumen.value = (
            f"Productos: {inventario.cantidad_productos()}   |   "
            f"Stock bajo: {inventario.cantidad_stock_bajo()}   |   "
            f"Valor total: ${inventario.valor_total_inventario():,.2f}"
        )
        actualizar_resumen_pila()

    def cargar_y_actualizar(producto: Producto) -> None:
        cargar_en_formulario(producto)
        mostrar_mensaje(f"Producto {producto.codigo} seleccionado.")
        page.update()

    def agregar_click(evento) -> None:
        try:
            producto = crear_desde_formulario()
            inventario.agregar_producto(producto)
            mostrar_mensaje(f"Producto {producto.codigo} agregado correctamente.")
            limpiar_formulario()
            actualizar_tabla()
        except ValidationError as error:
            mostrar_mensaje(mensaje_error_pydantic(error), True)
        except (OSError, ValueError) as error:
            mostrar_mensaje(str(error), True)
        page.update()

    def buscar_click(evento) -> None:
        try:
            if not (codigo.value or "").strip():
                raise ValueError("Ingrese el código que desea buscar.")
            producto = inventario.buscar_producto(codigo.value)
            cargar_en_formulario(producto)
            mostrar_mensaje(f"Producto {producto.codigo} encontrado.")
        except (KeyError, OSError, ValueError) as error:
            mostrar_mensaje(str(error).strip("'"), True)
        page.update()

    def actualizar_click(evento) -> None:
        try:
            if not (codigo.value or "").strip():
                raise ValueError(
                    "Busque o seleccione un producto antes de actualizarlo."
                )
            producto = inventario.actualizar_producto(
                codigo=codigo.value,
                nombre=nombre.value or "",
                categoria=categoria.value,
                cantidad=convertir_numero(cantidad.value, "La cantidad"),
                unidad=unidad.value,
                costo_unitario=convertir_numero(costo.value, "El costo unitario"),
                stock_minimo=convertir_numero(stock_minimo.value, "El stock mínimo"),
            )
            mostrar_mensaje(f"Producto {producto.codigo} actualizado correctamente.")
            limpiar_formulario()
            actualizar_tabla()
        except ValidationError as error:
            mostrar_mensaje(mensaje_error_pydantic(error), True)
        except (KeyError, OSError, ValueError) as error:
            mostrar_mensaje(str(error).strip("'"), True)
        page.update()

    def eliminar_click(evento) -> None:
        try:
            if not (codigo.value or "").strip():
                raise ValueError(
                    "Busque o seleccione un producto antes de eliminarlo."
                )
            eliminado = inventario.eliminar_producto(codigo.value)
            mostrar_mensaje(
                f"Producto {eliminado.codigo} eliminado y guardado en la pila."
            )
            limpiar_formulario()
            actualizar_tabla()
        except (IndexError, KeyError, OSError, ValueError) as error:
            mostrar_mensaje(str(error).strip("'"), True)
        page.update()

    def consultar_eliminado_click(evento) -> None:
        try:
            producto = inventario.consultar_ultimo_eliminado()
            mostrar_mensaje(
                f"Siguiente producto para restaurar: "
                f"{producto.codigo} - {producto.nombre}."
            )
        except IndexError as error:
            mostrar_mensaje(str(error), True)
        page.update()

    def restaurar_click(evento) -> None:
        try:
            producto = inventario.restaurar_ultimo_eliminado()
            mostrar_mensaje(
                f"Producto {producto.codigo} restaurado desde la pila correctamente."
            )
            limpiar_formulario()
            actualizar_tabla()
        except (IndexError, OSError, ValueError) as error:
            mostrar_mensaje(str(error), True)
        page.update()

    def cargar_datos_click(evento) -> None:
        try:
            agregados = 0
            for datos in DATOS_PRUEBA:
                producto = Producto(
                    codigo=datos[0],
                    nombre=datos[1],
                    categoria=datos[2],
                    cantidad=datos[3],
                    unidad=datos[4],
                    costo_unitario=datos[5],
                    stock_minimo=datos[6],
                )
                if not inventario.existe_producto(producto.codigo):
                    inventario.agregar_producto(producto)
                    agregados += 1
            mostrar_mensaje(
                f"Se cargaron {agregados} productos y se guardaron en JSON."
            )
            actualizar_tabla()
        except (OSError, ValueError) as error:
            mostrar_mensaje(str(error), True)
        page.update()

    def cambiar_filtro(evento) -> None:
        actualizar_tabla()
        page.update()

    filtro.on_select = cambiar_filtro

    formulario = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Datos del producto", size=20, weight=ft.FontWeight.BOLD),
                ft.ResponsiveRow(
                    controls=[
                        ft.Container(codigo, col={"sm": 12, "md": 4}),
                        ft.Container(nombre, col={"sm": 12, "md": 8}),
                        ft.Container(categoria, col={"sm": 12, "md": 4}),
                        ft.Container(cantidad, col={"sm": 12, "md": 4}),
                        ft.Container(unidad, col={"sm": 12, "md": 4}),
                        ft.Container(costo, col={"sm": 12, "md": 6}),
                        ft.Container(stock_minimo, col={"sm": 12, "md": 6}),
                    ]
                ),
                ft.Row(
                    controls=[
                        ft.Button("Agregar", icon=ft.Icons.ADD, on_click=agregar_click),
                        ft.Button("Buscar", icon=ft.Icons.SEARCH, on_click=buscar_click),
                        ft.Button(
                            "Actualizar", icon=ft.Icons.EDIT, on_click=actualizar_click
                        ),
                        ft.Button(
                            "Eliminar", icon=ft.Icons.DELETE, on_click=eliminar_click
                        ),
                        ft.OutlinedButton(
                            "Limpiar", icon=ft.Icons.CLEAR, on_click=limpiar_formulario
                        ),
                        ft.OutlinedButton(
                            "Cargar datos de prueba",
                            icon=ft.Icons.INVENTORY_2,
                            on_click=cargar_datos_click,
                        ),
                    ],
                    wrap=True,
                    spacing=10,
                    run_spacing=10,
                ),
                ft.Row(
                    controls=[
                        ft.OutlinedButton(
                            "Consultar último eliminado",
                            icon=ft.Icons.VISIBILITY,
                            on_click=consultar_eliminado_click,
                        ),
                        ft.Button(
                            "Restaurar último eliminado",
                            icon=ft.Icons.RESTORE,
                            on_click=restaurar_click,
                        ),
                    ],
                    wrap=True,
                    spacing=10,
                    run_spacing=10,
                ),
                estado_pila,
                mensaje,
            ],
            spacing=14,
        ),
        padding=18,
        border=ft.Border.all(1, ft.Colors.BLUE_GREY_100),
        border_radius=12,
        bgcolor=ft.Colors.WHITE,
    )

    page.add(
        ft.Text(
            "Inventario de restaurante de comida rápida",
            size=28,
            weight=ft.FontWeight.BOLD,
        ),
        ft.Text(
            "Inventario persistente y restauración LIFO de productos eliminados",
            color=ft.Colors.BLUE_GREY_700,
        ),
        estado_persistencia,
        formulario,
        ft.Divider(),
        ft.ResponsiveRow(
            controls=[
                ft.Container(
                    ft.Text(
                        "Productos registrados", size=20, weight=ft.FontWeight.BOLD
                    ),
                    col={"sm": 12, "md": 8},
                ),
                ft.Container(filtro, col={"sm": 12, "md": 4}),
            ]
        ),
        resumen,
        ft.Row([tabla], scroll=ft.ScrollMode.AUTO),
    )

    actualizar_tabla()


if __name__ == "__main__":
    ft.run(main)

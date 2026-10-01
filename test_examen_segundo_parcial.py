import pytest

from Garces_Karla_ExamenSegundoParcial import (
    InventarioRestaurante,
    PilaProductosEliminados,
    Producto,
    RepositorioArchivoJSON,
    RepositorioProductos,
    RepositorioProductosEliminados,
)


@pytest.fixture
def producto_pescado() -> Producto:
    return Producto(
        codigo="CON002",
        nombre="Pescado",
        categoria="Congelados",
        cantidad=4,
        unidad="Cajas",
        costo_unitario=48.00,
        stock_minimo=5,
    )


@pytest.fixture
def producto_onion_rings() -> Producto:
    return Producto(
        codigo="CON005",
        nombre="Onion rings",
        categoria="Congelados",
        cantidad=3,
        unidad="Cajas",
        costo_unitario=26.50,
        stock_minimo=4,
    )


@pytest.fixture
def pila() -> PilaProductosEliminados:
    return PilaProductosEliminados(2)


@pytest.fixture
def repositorio_eliminados() -> RepositorioProductosEliminados:
    return RepositorioProductosEliminados(2)


def test_pila_nueva_esta_vacia(pila):
    assert pila.esta_vacia()
    assert pila.get_cantidad() == 0


def test_apilar_aumenta_la_cantidad(pila, producto_pescado):
    pila.apilar(producto_pescado)

    assert not pila.esta_vacia()
    assert pila.get_cantidad() == 1


def test_ver_tope_consulta_sin_eliminar(pila, producto_pescado):
    pila.apilar(producto_pescado)

    assert pila.ver_tope() is producto_pescado
    assert pila.get_cantidad() == 1


def test_desapilar_respeta_orden_lifo(
    pila, producto_pescado, producto_onion_rings
):
    pila.apilar(producto_pescado)
    pila.apilar(producto_onion_rings)

    assert pila.desapilar() is producto_onion_rings
    assert pila.desapilar() is producto_pescado
    assert pila.esta_vacia()


def test_desapilar_pila_vacia_lanza_excepcion(pila):
    with pytest.raises(IndexError, match="No hay productos eliminados"):
        pila.desapilar()


def test_ver_tope_pila_vacia_lanza_excepcion(pila):
    with pytest.raises(IndexError, match="No hay productos eliminados"):
        pila.ver_tope()


def test_apilar_pila_llena_lanza_excepcion(
    pila, producto_pescado, producto_onion_rings
):
    tercer_producto = producto_pescado.model_copy(update={"codigo": "CON009"})
    pila.apilar(producto_pescado)
    pila.apilar(producto_onion_rings)

    with pytest.raises(IndexError, match="está llena"):
        pila.apilar(tercer_producto)


def test_capacidad_invalida_lanza_excepcion():
    with pytest.raises(ValueError, match="mayor que cero"):
        PilaProductosEliminados(0)


def test_repository_oculta_pila_y_retorna_ultimo_producto(
    repositorio_eliminados, producto_pescado, producto_onion_rings
):
    repositorio_eliminados.guardar(producto_pescado)
    repositorio_eliminados.guardar(producto_onion_rings)

    assert repositorio_eliminados.consultar_ultimo() is producto_onion_rings
    assert repositorio_eliminados.retirar_ultimo() is producto_onion_rings
    assert repositorio_eliminados.cantidad() == 1


def test_repositorio_productos_rechaza_codigo_duplicado(producto_pescado):
    repositorio = RepositorioProductos()
    repositorio.agregar(producto_pescado)

    with pytest.raises(ValueError, match="Ya existe un producto"):
        repositorio.agregar(producto_pescado.model_copy(deep=True))


def test_repositorio_productos_realiza_crud(producto_pescado):
    repositorio = RepositorioProductos()
    repositorio.agregar(producto_pescado)

    encontrado = repositorio.obtener("con002")
    actualizado = repositorio.actualizar(
        codigo="CON002",
        nombre="Filete de pescado",
        categoria="Congelados",
        cantidad=7,
        unidad="Cajas",
        costo_unitario=50,
        stock_minimo=5,
    )
    eliminado = repositorio.eliminar("CON002")

    assert encontrado is producto_pescado
    assert actualizado.nombre == "Filete De Pescado"
    assert actualizado.cantidad == 7
    assert eliminado is producto_pescado
    assert repositorio.cantidad() == 0


def test_eliminar_producto_lo_guarda_en_pila(producto_pescado):
    inventario = InventarioRestaurante(
        repositorio_eliminados=RepositorioProductosEliminados(2)
    )
    inventario.agregar_producto(producto_pescado)

    eliminado = inventario.eliminar_producto("CON002")

    assert eliminado is producto_pescado
    assert inventario.cantidad_productos() == 0
    assert inventario.cantidad_eliminados() == 1
    assert inventario.consultar_ultimo_eliminado() is producto_pescado


def test_restaurar_recupera_el_ultimo_producto_eliminado(
    producto_pescado, producto_onion_rings
):
    inventario = InventarioRestaurante(
        repositorio_eliminados=RepositorioProductosEliminados(2)
    )
    inventario.agregar_producto(producto_pescado)
    inventario.agregar_producto(producto_onion_rings)
    inventario.eliminar_producto("CON002")
    inventario.eliminar_producto("CON005")

    restaurado = inventario.restaurar_ultimo_eliminado()

    assert restaurado is producto_onion_rings
    assert inventario.existe_producto("CON005")
    assert not inventario.existe_producto("CON002")
    assert inventario.cantidad_eliminados() == 1


def test_no_elimina_si_la_pila_esta_llena(producto_pescado, producto_onion_rings):
    inventario = InventarioRestaurante(
        repositorio_eliminados=RepositorioProductosEliminados(1)
    )
    inventario.agregar_producto(producto_pescado)
    inventario.agregar_producto(producto_onion_rings)
    inventario.eliminar_producto("CON002")

    with pytest.raises(IndexError, match="pila de eliminados está llena"):
        inventario.eliminar_producto("CON005")

    assert inventario.existe_producto("CON005")


def test_filtro_stock_bajo(producto_pescado, producto_onion_rings):
    inventario = InventarioRestaurante()
    inventario.agregar_producto(producto_pescado)
    inventario.agregar_producto(producto_onion_rings)

    productos_bajos = inventario.listar_productos("Stock bajo")

    assert [producto.codigo for producto in productos_bajos] == ["CON002", "CON005"]


def test_persistencia_guarda_y_recupera_productos(tmp_path, producto_pescado):
    ruta = tmp_path / "inventario.json"
    inventario = InventarioRestaurante(
        persistencia=RepositorioArchivoJSON(ruta)
    )
    inventario.agregar_producto(producto_pescado)

    inventario_recuperado = InventarioRestaurante(
        persistencia=RepositorioArchivoJSON(ruta)
    )

    assert ruta.exists()
    assert inventario_recuperado.existe_producto("CON002")
    assert inventario_recuperado.buscar_producto("CON002").nombre == "Pescado"


def test_persistencia_conserva_la_pila_de_eliminados(
    tmp_path, producto_pescado, producto_onion_rings
):
    ruta = tmp_path / "inventario.json"
    inventario = InventarioRestaurante(
        repositorio_eliminados=RepositorioProductosEliminados(2),
        persistencia=RepositorioArchivoJSON(ruta),
    )
    inventario.agregar_producto(producto_pescado)
    inventario.agregar_producto(producto_onion_rings)
    inventario.eliminar_producto("CON002")
    inventario.eliminar_producto("CON005")

    inventario_recuperado = InventarioRestaurante(
        repositorio_eliminados=RepositorioProductosEliminados(2),
        persistencia=RepositorioArchivoJSON(ruta),
    )

    assert inventario_recuperado.cantidad_eliminados() == 2
    assert inventario_recuperado.consultar_ultimo_eliminado().codigo == "CON005"


def test_restauracion_persistente_se_conserva_al_reiniciar(
    tmp_path, producto_pescado
):
    ruta = tmp_path / "inventario.json"
    inventario = InventarioRestaurante(
        persistencia=RepositorioArchivoJSON(ruta)
    )
    inventario.agregar_producto(producto_pescado)
    inventario.eliminar_producto("CON002")
    inventario.restaurar_ultimo_eliminado()

    inventario_recuperado = InventarioRestaurante(
        persistencia=RepositorioArchivoJSON(ruta)
    )

    assert inventario_recuperado.existe_producto("CON002")
    assert inventario_recuperado.cantidad_eliminados() == 0


def test_archivo_json_invalido_lanza_error(tmp_path):
    ruta = tmp_path / "inventario.json"
    ruta.write_text("contenido inválido", encoding="utf-8")

    with pytest.raises(ValueError, match="no contiene un JSON válido"):
        InventarioRestaurante(persistencia=RepositorioArchivoJSON(ruta))

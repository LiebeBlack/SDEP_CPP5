"""Pruebas del gestor de documentos (document_manager.py)"""

import os
import time

from src.utils.document_manager import DocumentManager


def _crear_manager(storage):
    """Crea un DocumentManager apuntando a los directorios temporales"""
    manager = DocumentManager()
    # Los directorios ya quedan redirigidos por el fixture `storage`
    return manager


def test_save_document(storage):
    manager = _crear_manager(storage)
    ruta, nombre = manager.save_document(b"contenido-pdf", "planilla.pdf", "laboral")
    assert nombre.endswith(".pdf")
    assert os.path.exists(ruta)
    assert "laboral" in ruta
    assert manager.get_document(ruta) == b"contenido-pdf"


def test_save_photo(storage):
    manager = _crear_manager(storage)
    ruta, nombre = manager.save_photo(b"imagen", "foto.png", 7)
    assert nombre.endswith(".png")
    assert os.path.exists(ruta)
    assert str(7) in ruta


def test_get_document_inexistente(storage):
    manager = _crear_manager(storage)
    assert manager.get_document("/ruta/que/no/existe.pdf") is None


def test_delete_document(storage):
    manager = _crear_manager(storage)
    ruta, _ = manager.save_document(b"datos", "doc.pdf", "general")
    assert manager.delete_document(ruta)
    assert not os.path.exists(ruta)
    # La carpeta de categoría queda vacía y se elimina
    assert not os.path.exists(os.path.dirname(ruta))


def test_delete_document_inexistente(storage):
    manager = _crear_manager(storage)
    assert not manager.delete_document("/no/existe.pdf")


def test_copy_document(storage):
    manager = _crear_manager(storage)
    origen, _ = manager.save_document(b"abc", "orig.pdf", "general")
    destino = os.path.join(storage, "copia.pdf")
    assert manager.copy_document(origen, destino)
    assert os.path.exists(destino)
    assert not manager.copy_document("/no/existe", "/tampoco")


def test_move_document(storage):
    manager = _crear_manager(storage)
    origen, _ = manager.save_document(b"abc", "orig.pdf", "general")
    destino = os.path.join(storage, "movido.pdf")
    assert manager.move_document(origen, destino)
    assert os.path.exists(destino)
    assert not os.path.exists(origen)
    assert not manager.move_document("/no/existe", "/tampoco")


def test_get_file_info(storage):
    manager = _crear_manager(storage)
    ruta, _ = manager.save_document(b"datos", "planilla.pdf", "general")
    info = manager.get_file_info(ruta)
    assert info is not None
    assert info["name"] == os.path.basename(ruta)
    assert info["size"] == 5
    assert info["is_pdf"] is True
    assert info["is_image"] is False
    assert info["mime_type"] == "application/pdf"
    assert manager.get_file_info("/no/existe.pdf") is None


def test_list_documents(storage):
    manager = _crear_manager(storage)
    manager.save_document(b"a", "uno.pdf", "laboral")
    manager.save_document(b"bb", "dos.pdf", "general")
    todos = manager.list_documents()
    assert len(todos) == 2
    laboral = manager.list_documents("laboral")
    assert len(laboral) == 1
    assert manager.list_documents("inexistente") == []


def test_list_employee_photos(storage):
    manager = _crear_manager(storage)
    manager.save_photo(b"foto", "perfil.jpg", 3)
    manager.save_document(b"doc", "planilla.pdf", "general")
    fotos = manager.list_employee_photos(3)
    assert len(fotos) == 1
    assert fotos[0]["is_image"] is True
    assert manager.list_employee_photos(999) == []


def test_get_document_url(storage):
    manager = _crear_manager(storage)
    ruta, _ = manager.save_document(b"x", "doc.pdf", "general")
    url = manager.get_document_url(ruta)
    assert url.startswith("file:///")


def test_validate_file(storage):
    manager = _crear_manager(storage)
    ok, msg = manager.validate_file(b"datos", "doc.pdf")
    assert ok and msg == ""
    ok, msg = manager.validate_file(b"datos", "virus.exe")
    assert not ok and "Tipo de archivo no permitido" in msg
    ok, msg = manager.validate_file(b"x" * (51 * 1024 * 1024), "doc.pdf")
    assert not ok and "excede el tamaño máximo" in msg


def test_export_file(storage):
    manager = _crear_manager(storage)
    ruta, nombre = manager.export_file(b"exportado", "reporte.csv", "reportes")
    assert os.path.exists(ruta)
    assert nombre.endswith(".csv")


def test_cleanup_old_files(storage):
    manager = _crear_manager(storage)
    ruta_viejo, _ = manager.save_document(b"viejo", "viejo.pdf", "general")
    # Envejecer el archivo
    antiguo = time.time() - (60 * 24 * 60 * 60)  # 60 días
    os.utime(ruta_viejo, (antiguo, antiguo))
    # Archivo reciente no debe eliminarse
    manager.save_document(b"nuevo", "nuevo.pdf", "general")
    eliminados = manager.cleanup_old_files(days=30)
    assert eliminados == 1
    assert not os.path.exists(ruta_viejo)


def test_get_storage_stats(storage):
    manager = _crear_manager(storage)
    manager.save_document(b"abcd", "doc.pdf", "general")
    manager.save_photo(b"foto", "perfil.png", 1)
    stats = manager.get_storage_stats()
    assert stats["documents_count"] == 1
    assert stats["photos_count"] == 1
    assert stats["total_size"] > 0
    assert stats["total_size_formatted"].endswith("B")
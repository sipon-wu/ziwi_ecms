"""知微能碳 — 数据导入 API"""
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import FileResponse
from db import ok, err
from data_import import import_excel, generate_template_excel, list_importable_tables, TEMPLATES
import tempfile, os

router = APIRouter(prefix="/api/import", tags=["数据导入"])


@router.get("/tables")
def import_tables_list():
    return ok({"tables": list_importable_tables()})


@router.post("/{table_name}")
async def import_table(table_name: str, file: UploadFile = File(...)):
    if not file.filename.endswith((".xlsx", ".xls")):
        return err("仅支持 .xlsx 格式")
    suffix = ".xlsx" if file.filename.endswith(".xlsx") else ".xls"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    try:
        result, error = import_excel(tmp_path, table_name)
        if error:
            return err(str(error))
        return ok(result)
    finally:
        try:
            os.unlink(tmp_path)
        except:
            pass


@router.get("/{table_name}/template")
def download_template(table_name: str):
    if table_name not in TEMPLATES:
        return err(f"不支持的表名：{table_name}")
    wb = generate_template_excel(table_name)
    if wb is None:
        return err("生成模板失败")
    tmp_path = os.path.join(tempfile.gettempdir(), f"template_{table_name}.xlsx")
    wb.save(tmp_path)
    info = TEMPLATES[table_name]
    return FileResponse(tmp_path, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        filename=f"知微能碳-导入模板-{info['title']}.xlsx")

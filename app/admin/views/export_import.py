"""
Экспорт и импорт данных
"""

from flask import render_template, flash, redirect, url_for, request, jsonify, send_file, session
from flask_login import login_required
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import csv
import io

from ..decorators import admin_required
from ..export_service import ExportService
from ..import_service import ImportService


@login_required
@admin_required
def export_data():
    """Страница экспорта данных"""
    try:
        export_service = ExportService()
        export_options = export_service.get_available_exports()

        export_files = _get_export_files(export_service.export_dir)

        return render_template('admin/export.html',
                               export_options=export_options,
                               export_files=export_files)

    except Exception as e:
        flash(f'Ошибка при загрузке страницы экспорта: {str(e)}', 'danger')
        return redirect(url_for('admin.dashboard'))


def _get_export_files(export_dir):
    """Получить список файлов экспорта"""
    export_files = []

    if os.path.exists(export_dir):
        for filename in os.listdir(export_dir):
            filepath = os.path.join(export_dir, filename)
            if os.path.isfile(filepath):
                stat = os.stat(filepath)
                export_files.append({
                    'name': filename,
                    'size': stat.st_size,
                    'created': datetime.fromtimestamp(stat.st_ctime),
                    'type': 'csv' if filename.endswith('.csv') else 'zip'
                })

    export_files.sort(key=lambda x: x['created'], reverse=True)
    return export_files


@login_required
@admin_required
def download_export(filename):
    """Скачать файл экспорта"""
    try:
        safe_filename = secure_filename(filename)
        if not safe_filename:
            flash('Неверное имя файла', 'danger')
            return redirect(url_for('admin.export_data'))

        export_service = ExportService()
        filepath = os.path.join(export_service.export_dir, safe_filename)

        if not filepath.startswith(export_service.export_dir):
            flash('Неверный путь к файлу', 'danger')
            return redirect(url_for('admin.export_data'))

        if not os.path.exists(filepath):
            flash(f'Файл {safe_filename} не найден', 'danger')
            return redirect(url_for('admin.export_data'))

        if safe_filename.endswith('.csv'):
            mimetype = 'text/csv'
        elif safe_filename.endswith('.zip'):
            mimetype = 'application/zip'
        else:
            mimetype = 'application/octet-stream'

        return send_file(
            filepath,
            as_attachment=True,
            download_name=safe_filename,
            mimetype=mimetype
        )

    except Exception as e:
        flash(f'Ошибка при скачивании файла: {str(e)}', 'danger')
        return redirect(url_for('admin.export_data'))


@login_required
@admin_required
def generate_export():
    """Генерация нового экспорта"""
    try:
        export_type = request.form.get('export_type')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        custom_name = request.form.get('custom_name', '').strip()

        export_service = ExportService()

        export_service.cleanup_old_exports(days_to_keep=7)

        export_handlers = {
            'users': lambda: export_service.export_users_to_csv(custom_name),
            'products': lambda: export_service.export_products_to_csv(custom_name),
            'orders': lambda: export_service.export_orders_to_csv(start_date, end_date, custom_name),
            'full': lambda: export_service.export_full_backup(custom_name),
            'categories': lambda: export_service.export_table_to_csv('categories', custom_name),
            'brands': lambda: export_service.export_table_to_csv('shop_brand', custom_name),
        }

        handler = export_handlers.get(export_type)
        if not handler:
            flash('Неверный тип экспорта', 'danger')
            return redirect(url_for('admin.export_data'))

        result = handler()

        if result['success']:
            flash(result['message'], 'success')
        else:
            flash(result['message'], 'danger')

        return redirect(url_for('admin.export_data'))

    except Exception as e:
        flash(f'Ошибка при генерации экспорта: {str(e)}', 'danger')
        return redirect(url_for('admin.export_data'))


@login_required
@admin_required
def delete_export(filename):
    """Удаление файла экспорта"""
    try:
        safe_filename = secure_filename(filename)
        if not safe_filename:
            flash('Неверное имя файла', 'danger')
            return redirect(url_for('admin.export_data'))

        export_service = ExportService()
        filepath = os.path.join(export_service.export_dir, safe_filename)

        if not filepath.startswith(export_service.export_dir):
            flash('Неверный путь к файлу', 'danger')
            return redirect(url_for('admin.export_data'))

        if os.path.exists(filepath):
            os.remove(filepath)
            flash(f'Файл {safe_filename} успешно удален', 'success')
        else:
            flash('Файл не найден', 'danger')

        return redirect(url_for('admin.export_data'))

    except Exception as e:
        flash(f'Ошибка при удалении файла: {str(e)}', 'danger')
        return redirect(url_for('admin.export_data'))


@login_required
@admin_required
def quick_export():
    """Быстрый экспорт через API"""
    try:
        data = request.get_json()
        export_type = data.get('type')

        if not export_type:
            return jsonify({'success': False, 'message': 'Тип экспорта не указан'})

        export_service = ExportService()

        quick_export_handlers = {
            'users': export_service.export_users_to_csv,
            'products': export_service.export_products_to_csv,
            'full': export_service.export_full_backup,
        }

        handler = quick_export_handlers.get(export_type)
        if not handler:
            return jsonify({'success': False, 'message': 'Неверный тип экспорта'})

        result = handler()

        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message'],
                'filename': result['filename'],
                'download_url': url_for('admin.download_export', filename=result['filename'])
            })
        else:
            return jsonify({'success': False, 'message': result['message']})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {str(e)}'})


@login_required
@admin_required
def import_data():
    """Страница импорта данных"""
    try:
        import_service = ImportService()
        templates = import_service.get_import_templates()

        return render_template('admin/import.html',
                               templates=templates)

    except ImportError:
        flash('Сервис импорта не настроен', 'warning')
        templates = {}
        return render_template('admin/import.html',
                               templates=templates)
    except Exception as e:
        flash(f'Ошибка при загрузке страницы импорта: {str(e)}', 'danger')
        return redirect(url_for('admin.dashboard'))


@login_required
@admin_required
def download_import_template(template_type):
    """Скачать шаблон для импорта"""
    try:
        import_service = ImportService()

        valid_templates = ['users', 'products', 'categories', 'brands']
        if template_type not in valid_templates:
            flash('Неверный тип шаблона', 'danger')
            return redirect(url_for('admin.import_data'))

        filepath = import_service.create_template_file(template_type)

        if not filepath or not os.path.exists(filepath):
            flash('Шаблон не найден', 'danger')
            return redirect(url_for('admin.import_data'))

        filename = os.path.basename(filepath)

        return send_file(
            filepath,
            as_attachment=True,
            download_name=filename,
            mimetype='text/csv'
        )

    except Exception as e:
        flash(f'Ошибка при создании шаблона: {str(e)}', 'danger')
        return redirect(url_for('admin.import_data'))


@login_required
@admin_required
def upload_import():
    """Загрузка и обработка CSV файла"""
    try:
        import_type = request.form.get('import_type')
        update_existing = 'update_existing' in request.form

        if 'csv_file' not in request.files:
            flash('Файл не выбран', 'danger')
            return redirect(url_for('admin.import_data'))

        file = request.files['csv_file']

        if file.filename == '':
            flash('Файл не выбран', 'danger')
            return redirect(url_for('admin.import_data'))

        if not file.filename.lower().endswith('.csv'):
            flash('Поддерживаются только CSV файлы', 'danger')
            return redirect(url_for('admin.import_data'))

        safe_filename = secure_filename(file.filename)
        import_service = ImportService()

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"import_{timestamp}_{safe_filename}"
        filepath = os.path.join(import_service.import_dir, filename)
        file.save(filepath)

        import_handlers = {
            'users': lambda: import_service.import_users_from_csv(filepath, update_existing),
            'products': lambda: import_service.import_products_from_csv(filepath, update_existing),
            'categories': lambda: import_service.import_categories_from_csv(filepath, update_existing),
            'brands': lambda: import_service.import_brands_from_csv(filepath, update_existing),
        }

        handler = import_handlers.get(import_type)
        if not handler:
            try:
                os.remove(filepath)
            except:
                pass
            flash('Неверный тип импорта', 'danger')
            return redirect(url_for('admin.import_data'))

        result = handler()

        try:
            os.remove(filepath)
        except:
            pass

        if result['success']:
            flash(result['message'], 'success')
        else:
            flash(result['message'], 'danger')

        return redirect(url_for('admin.import_data'))

    except Exception as e:
        flash(f'Ошибка при импорте данных: {str(e)}', 'danger')
        return redirect(url_for('admin.import_data'))


@login_required
@admin_required
def view_import_errors():
    """Просмотр ошибок импорта"""
    errors = session.get('import_errors', [])
    return render_template('admin/import_errors.html', errors=errors)


@login_required
@admin_required
def preview_import():
    """Предпросмотр CSV файла"""
    try:
        if 'csv_file' not in request.files:
            return jsonify({'success': False, 'message': 'Файл не выбран'})

        file = request.files['csv_file']

        if file.filename == '':
            return jsonify({'success': False, 'message': 'Файл не выбран'})

        if not file.filename.lower().endswith('.csv'):
            return jsonify({'success': False, 'message': 'Поддерживаются только CSV файлы'})

        content = file.read().decode('utf-8')
        lines = content.split('\n')[:11]

        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(lines[0] if lines else '')

        csv_data = []
        reader = csv.reader(io.StringIO('\n'.join(lines)), dialect)

        for i, row in enumerate(reader):
            if i < 10:
                csv_data.append(row)
            else:
                break

        return jsonify({
            'success': True,
            'data': csv_data,
            'row_count': len(csv_data) - 1 if csv_data else 0,
            'column_count': len(csv_data[0]) if csv_data else 0
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка предпросмотра: {str(e)}'})

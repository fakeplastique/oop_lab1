import asyncio
import logging

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from typing import Any

from ..auth.google_auth_service import GoogleAuthService


logger = logging.getLogger(__name__)


class GoogleDriveStorage:
    """
    Сервіс для роботи з Google Drive та Google Sheets API.

    Надає методи для:
    - Отримання списку Google Sheets файлів
    - Завантаження даних в Google Sheets
    - Скачування даних з Google Sheets
    """

    def __init__(self, auth_service: GoogleAuthService):
        """
        Ініціалізує сервіс Google Drive Storage.

        Args:
            auth_service: Сервіс автентифікації
        """
        self.auth_service = auth_service
        self._drive_service = None
        self._sheets_service = None

    def _get_drive_service(self):
        """Повертає сервіс Google Drive API."""
        if not self._drive_service:
            creds = self.auth_service.get_credentials()
            self._drive_service = build('drive', 'v3', credentials=creds)
        return self._drive_service

    def _get_sheets_service(self):
        """Повертає сервіс Google Sheets API."""
        if not self._sheets_service:
            creds = self.auth_service.get_credentials()
            self._sheets_service = build('sheets', 'v4', credentials=creds)
        return self._sheets_service

    async def list_spreadsheets(self) -> list[dict[str, str]]:
        """
        Отримує список всіх Google Sheets файлів користувача.

        Returns:
            list[dict]: Список словників з інформацією про файли:
                - id: ID файлу
                - name: Назва файлу
                - modifiedTime: Час останньої модифікації

        Raises:
            Exception: Якщо виникла помилка при отриманні списку файлів
        """
        loop = asyncio.get_event_loop()

        try:
            drive_service = self._get_drive_service()

            response = await loop.run_in_executor(
                None,
                lambda: drive_service.files().list(
                    q="mimeType='application/vnd.google-apps.spreadsheet'",
                    spaces='drive',
                    fields='files(id, name, modifiedTime)',
                    orderBy='modifiedTime desc'
                ).execute()
            )

            files = response.get('files', [])
            logger.info(f"Знайдено {len(files)} Google Sheets файлів")

            return files

        except HttpError as error:
            logger.error(f"Помилка при отриманні списку файлів: {error}")
            raise Exception(f"Не вдалося отримати список файлів: {error}")

    async def download_spreadsheet(self, file_id: str) -> dict[str, Any]:
        """
        Завантажує дані з Google Sheets файлу.

        Args:
            file_id: ID файлу Google Sheets

        Returns:
            dict: Дані таблиці у форматі:
                {
                    'rows': int,
                    'columns': int,
                    'cells': list[dict]
                }

        Raises:
            Exception: Якщо виникла помилка при завантаженні
        """
        loop = asyncio.get_event_loop()

        try:
            sheets_service = self._get_sheets_service()

            spreadsheet = await loop.run_in_executor(
                None,
                lambda: sheets_service.spreadsheets().get(
                    spreadsheetId=file_id
                ).execute()
            )

            sheet_name = spreadsheet['sheets'][0]['properties']['title']

            result = await loop.run_in_executor(
                None,
                lambda: sheets_service.spreadsheets().values().get(
                    spreadsheetId=file_id,
                    range=sheet_name
                ).execute()
            )

            values = result.get('values', [])

            data = self._convert_from_sheets_format(values)

            logger.info(f"Завантажено таблицю {file_id}: {data['rows']}x{data['columns']}")

            return data

        except HttpError as error:
            logger.error(f"Помилка при завантаженні файлу {file_id}: {error}")
            raise Exception(f"Не вдалося завантажити файл: {error}")

    async def upload_spreadsheet(
        self,
        data: dict[str, Any],
        file_name: str,
        file_id: str | None = None
    ) -> str:
        """
        Завантажує дані в Google Sheets.

        Args:
            data: Дані таблиці у форматі {'rows': int, 'columns': int, 'cells': list}
            file_name: Назва файлу
            file_id: ID існуючого файлу (якщо потрібно оновити), None для нового файлу

        Returns:
            str: ID створеного/оновленого файлу

        Raises:
            Exception: Якщо виникла помилка при завантаженні
        """
        loop = asyncio.get_event_loop()

        try:
            sheets_service = self._get_sheets_service()
            drive_service = self._get_drive_service()

            values = self._convert_to_sheets_format(data)

            if file_id:
                await self._update_spreadsheet(file_id, values, data['rows'], data['columns'])
                logger.info(f"Оновлено файл {file_id}")
                return file_id
            else:
                spreadsheet = {
                    'properties': {
                        'title': file_name
                    },
                    'sheets': [{
                        'properties': {
                            'title': 'Sheet1',
                            'gridProperties': {
                                'rowCount': max(data['rows'], 10),
                                'columnCount': max(data['columns'], 10)
                            }
                        }
                    }]
                }

                result = await loop.run_in_executor(
                    None,
                    lambda: sheets_service.spreadsheets().create(
                        body=spreadsheet,
                        fields='spreadsheetId,sheets.properties.title'
                    ).execute()
                )

                new_file_id = result.get('spreadsheetId')
                sheet_name = result['sheets'][0]['properties']['title']

                if values:
                    await loop.run_in_executor(
                        None,
                        lambda: sheets_service.spreadsheets().values().update(
                            spreadsheetId=new_file_id,
                            range=f'{sheet_name}!A1',
                            valueInputOption='USER_ENTERED',
                            body={'values': values}
                        ).execute()
                    )

                logger.info(f"Створено новий файл {new_file_id} з назвою '{file_name}'")
                return new_file_id

        except HttpError as error:
            logger.error(f"Помилка при завантаженні файлу: {error}")
            raise Exception(f"Не вдалося завантажити файл: {error}")

    async def _update_spreadsheet(
        self,
        file_id: str,
        values: list[list[str]],
        rows: int,
        columns: int
    ) -> None:
        """
        Оновлює існуючий spreadsheet.

        Args:
            file_id: ID файлу
            values: Значення для запису
            rows: Кількість рядків
            columns: Кількість колонок
        """
        loop = asyncio.get_event_loop()
        sheets_service = self._get_sheets_service()

        spreadsheet = await loop.run_in_executor(
            None,
            lambda: sheets_service.spreadsheets().get(
                spreadsheetId=file_id
            ).execute()
        )

        sheet_name = spreadsheet['sheets'][0]['properties']['title']

        await loop.run_in_executor(
            None,
            lambda: sheets_service.spreadsheets().values().clear(
                spreadsheetId=file_id,
                range=sheet_name,
                body={}
            ).execute()
        )

        if values:
            await loop.run_in_executor(
                None,
                lambda: sheets_service.spreadsheets().values().update(
                    spreadsheetId=file_id,
                    range=f'{sheet_name}!A1',
                    valueInputOption='USER_ENTERED',
                    body={'values': values}
                ).execute()
            )

    def _convert_to_sheets_format(self, data: dict[str, Any]) -> list[list[str]]:
        """
        Конвертує дані з нашого формату в формат Google Sheets.

        Args:
            data: Дані у форматі {'rows': int, 'columns': int, 'cells': list}

        Returns:
            list[list[str]]: 2D масив значень
        """
        rows = data['rows']
        columns = data['columns']

        values = [['' for _ in range(columns)] for _ in range(rows)]

        for cell in data['cells']:
            row = cell['row']
            col = cell['col']
            expression = cell['expression']

            if 0 <= row < rows and 0 <= col < columns:
                values[row][col] = expression

        return values

    def _convert_from_sheets_format(self, values: list[list[str]]) -> dict[str, Any]:
        """
        Конвертує дані з формату Google Sheets в наш формат.

        Args:
            values: 2D масив значень з Google Sheets

        Returns:
            dict: Дані у форматі {'rows': int, 'columns': int, 'cells': list}
        """
        if not values:
            return {
                'rows': 10,
                'columns': 10,
                'cells': []
            }

        rows = len(values)
        columns = max(len(row) for row in values) if values else 0

        cells = []
        for row_idx, row in enumerate(values):
            for col_idx, value in enumerate(row):
                if value:  
                    cells.append({
                        'row': row_idx,
                        'col': col_idx,
                        'expression': value
                    })

        return {
            'rows': max(rows, 10),
            'columns': max(columns, 10),
            'cells': cells
        }

    async def delete_spreadsheet(self, file_id: str) -> None:
        """
        Видаляє Google Sheets файл.

        Args:
            file_id: ID файлу для видалення

        Raises:
            Exception: Якщо виникла помилка при видаленні
        """
        loop = asyncio.get_event_loop()

        try:
            drive_service = self._get_drive_service()

            await loop.run_in_executor(
                None,
                lambda: drive_service.files().delete(
                    fileId=file_id
                ).execute()
            )

            logger.info(f"Видалено файл {file_id}")

        except HttpError as error:
            logger.error(f"Помилка при видаленні файлу {file_id}: {error}")
            raise Exception(f"Не вдалося видалити файл: {error}")
        

    def reset_services(self):
        """Скидає кешовані об'єкти сервісів Google Drive та Sheets."""
        self._drive_service = None
        self._sheets_service = None

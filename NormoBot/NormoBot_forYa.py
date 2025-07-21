import json
import traceback
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import g4f
from pathlib import Path
import PyPDF2
import os
import asyncio
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Конфигурация
CONFIG = {
    "llm_model": "gpt-4.1-mini",
    "retry_attempts": 3,
    "retry_interval": 5,
    "llm_timeout": 120,
    "max_file_size": 20 * 1024 * 1024,
    "telegram_timeout": 60,
    "max_message_length": 4000
}

class NormalControllerBot:
    def __init__(self, token: str):
        self.token = token
        self.application = Application.builder().token(self.token).read_timeout(CONFIG["telegram_timeout"]).write_timeout(CONFIG["telegram_timeout"]).build()
        self.setup_handlers()
    
    async def initialize(self):
        await self.application.initialize()
        await self.application.start()
    
    def setup_handlers(self):
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
        self.application.add_handler(MessageHandler(filters.Document.ALL, self.handle_document))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "Привет! Я нормоконтролёр для проверки технических заданий. "
            "Отправьте текст ТЗ или прикрепите файл (PDF, TXT)."
        )

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text
        await update.message.reply_text("Проверяю ваше техническое задание...")
        analysis = await self.analyze_tz(text)
        await self.send_analysis(update, analysis)

    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        document = update.message.document
        if document.file_size > CONFIG["max_file_size"]:
            await update.message.reply_text("Файл слишком большой. Максимальный размер: 20 МБ.")
            return
        file = await document.get_file()
        file_path = f"/tmp/temp_{document.file_id}"
        try:
            await file.download_to_drive(file_path)
            file_text = self.extract_text_from_file(file_path, document.mime_type)
            message_text = update.message.text or ""
            combined_text = f"{message_text}\n\n{file_text}" if message_text else file_text
            await update.message.reply_text("Проверяю ваше техническое задание...")
            analysis = await self.analyze_tz(combined_text)
            await self.send_analysis(update, analysis)
        except Exception as e:
            await update.message.reply_text("Ошибка при обработке файла. Попробуйте отправить другой файл (PDF или TXT).")
        finally:
            if Path(file_path).exists():
                Path(file_path).unlink()

    def extract_text_from_file(self, file_path: str, mime_type: str) -> str:
        try:
            file_ext = Path(file_path).suffix.lower()
            if mime_type == "application/pdf" or file_ext == ".pdf":
                with open(file_path, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    text = ""
                    for page in reader.pages:
                        extracted = page.extract_text()
                        if extracted:
                            text += extracted
                    return text
            elif mime_type == "text/plain" or file_ext == ".txt":
                with open(file_path, "r", encoding="utf-8") as f:
                    return f.read()
            else:
                raise ValueError("Неподдерживаемый формат файла. Используйте PDF или TXT.")
        except Exception as e:
            raise

    async def analyze_tz(self, text: str) -> str:
        prompt = """
        ### Промпт для нормоконтроля технического задания

        ### Роль
        Вы — нормоконтролер, специализирующийся на проверке технических заданий (ТЗ) на соответствие ГОСТам и лучшим практикам технической документации.

        ### Задача
        Проанализируйте предоставленное техническое задание, выявите ошибки, несоответствия или отклонения от требуемых стандартов и предложите исправления в формате: «Было / Замечание / Должно быть».

        ### Инструкции

        #### Проверка структуры
        Убедитесь, что проектная (конструкторская) документация на разработку аккумуляторной батареи для электроавтомобиля содержит все необходимые разделы в соответствии с ГОСТ 15.016-2016 и другими применимыми нормативными документами, включая, но не ограничиваясь:
        - ГОСТ 15.016-2016 — Система разработки и постановки продукции на производство. Проектная документация  
        - ГОСТ Р 53778-2010 — Аккумуляторные батареи. Общие технические условия  
        - ГОСТ Р 52350.11-2005 — Безопасность электрического оборудования. Требования к аккумуляторным батареям  
        - ГОСТ 12.2.007.0-75 — Электробезопасность  
        - ГОСТ 30804.4.2-2013 и ГОСТ 30804.4.3-2013 — Электромагнитная совместимость  
        - ГОСТ 12.1.044-89 — Пожарная безопасность  
        - Правила устройства электроустановок (ПУЭ)  
        - НПБ 105-03 — Нормы пожарной безопасности для аккумуляторных помещений  
        - ISO 12405 и/или IEC 62660 (при использовании международных стандартов)

        Типичные обязательные разделы документации включают:
        - Введение  
        - Наименование, основание и сроки разработки  
        - Цель разработки, наименование и обозначение изделия  
        - Технические требования к изделию  
        - Требования к сырью и материалам  
        - Требования к консервации, упаковке и маркировке  
        - Требования к учебно-тренировочным средствам (при необходимости)  
        - Специальные требования (безопасность, экология, электромагнитная совместимость)  
        - Требования к документации  
        - Этапы выполнения разработки с указанием сроков и ответственных  
        - Порядок выполнения и приемки этапов разработки  
        - Примечания и дополнительные указания  

        Проверьте наличие всех обязательных разделов, отметьте отсутствие необходимых и наличие избыточных разделов, а также соответствие содержания требованиям нормативных документов и специфике разработки АКБ для электроавтомобиля.

        #### Проверка содержания
        Проверьте, что все указанные стандарты ГОСТ и нормативные документы актуальны и правильно указаны. Убедитесь, что требования конкретны, измеримы, достижимы, релевантны и ограничены по времени (SMART). Проверьте отсутствие противоречивых или неоднозначных утверждений. Подтвердите, что все технические параметры указаны точно и полно, включая:
        - Номинальное напряжение аккумулятора и отдельных элементов (например, 12 В на элемент, 192 В на батарею из 16 элементов)
        - Емкость аккумулятора (в ампер-часах), определяющая запас энергии
        - Тип аккумуляторов (свинцово-кислотные, литий-ионные и др.) и их конструктивные особенности
        - Количество и схема соединения элементов (последовательное, параллельное подключение)
        - Ток заряда и разряда, включая максимальные пиковые токи и пусковые токи оборудования
        - Требования к качеству электропитания — стабильность напряжения и частоты, допустимые отклонения
        - Рабочая температура и условия эксплуатации аккумуляторов
        - Требования к системам контроля и безопасности — наличие систем мониторинга состояния (PCM), защита от перегрузок и коротких замыканий
        - Требования к производственной документации — чертежи, спецификации, инструкции по эксплуатации
        - Испытания и контроль качества — проверка емкости, напряжения, надежности и безопасности
        - Требования к монтажу и обслуживанию, включая условия установки и вентиляции аккумуляторных помещений
        - Сроки изготовления и поставки
        - Соответствие нормативам и стандартам (например, ГОСТ, ПУЭ, НПБ 105-03)
        1. Требования к габаритам и массе аккумуляторной батареи — размеры, вес, что важно для интеграции в конструкцию автомобиля.
        2. Условия транспортировки и хранения — температурные режимы, влажность, вибрации и удары.
        3. Энергоэффективность и коэффициент полезного действия батареи.
        4. Срок службы и циклы заряда-разряда — гарантийные показатели долговечности.
        5. Требования к системе охлаждения — тип, эффективность, способы реализации.
        6. Электромагнитная совместимость (EMC) — требования к помехозащищенности и излучению.
        7. Требования к программному обеспечению систем управления батареей (BMS) — алгоритмы управления, диагностика и обновление ПО.
        8. Требования к утилизации и экологической безопасности — материалы, возможность переработки.
        9. Требования к маркировке и идентификации элементов и сборок.
        10. Требования к документации по безопасности при аварийных ситуациях — инструкции по действиям при возгорании, утечках и т.п.
        11. Требования к совместимости с другими системами автомобиля — интерфейсы, протоколы обмена данными.
        12. Требования к испытаниям на вибрацию, удар, коррозию и другие механические воздействия.

        Проверка максимизации емкости АКБ относительно массы и актуальности технологии:
        1. Оцените используемую технологию производства аккумуляторных элементов с точки зрения удельной емкости (емкость на единицу массы, Ач/кг).  
        2. Проверьте соответствие выбранных материалов и химических составов современным достижениям в области аккумуляторных технологий (например, литий-ионные, твердотельные, литий-железо-фосфатные и др.).  
        3. Проанализируйте конструктивные решения, влияющие на снижение массы батареи при сохранении или увеличении емкости (например, использование легких корпусов, оптимизация толщины электродов, компоновка элементов).  
        4. Оцените технологию сборки и контроля качества, обеспечивающую максимальную плотность энергии и минимальные потери.  
        5. Проверьте наличие данных по испытаниям и подтверждению удельной емкости, включая сравнительный анализ с аналогичными технологиями на рынке.  
        6. Оцените актуальность технологии с учетом последних тенденций и инноваций в области аккумуляторных систем для электромобилей (например, исследования и внедрение новых материалов, технологий производства, систем управления батареей).  
        7. Проверьте соответствие технологии требованиям безопасности, долговечности и экологичности при максимальной емкости и минимальной массе.  
        8. Оцените перспективы масштабирования и серийного производства с сохранением заявленных параметров.

        Чек-лист проверки АКБ по температуре эксплуатации, вибрации и механическим воздействиям:
        1. Температура эксплуатации
        - Указан диапазон рабочих температур (минимальная, максимальная, оптимальная).  
        - Диапазон температур соответствует условиям эксплуатации электроавтомобиля (климатические зоны, сезонные колебания).  
        - Присутствуют данные по устойчивости к экстремальным температурам (низкие и высокие температуры).  
        - Описаны системы терморегуляции и охлаждения, их эффективность и характеристики.  
        - Приведены результаты испытаний на работоспособность и безопасность при различных температурах.  
        - Оценено влияние температуры на емкость, срок службы, безопасность и скорость заряда/разряда.  
        - Указаны требования к хранению и транспортировке с учетом температурных ограничений.  
        - Соответствие температурных параметров требованиям нормативных документов (ГОСТ, ISO, IEC и др.).
        2. Вибрация
        - Указаны параметры вибрационных испытаний (частотные диапазоны, амплитуды).  
        - Проведены испытания на вибрационную устойчивость в соответствии с эксплуатационными условиями автомобиля.  
        - Описаны конструктивные решения и методы защиты от вибраций.  
        - Приведены результаты испытаний и сертификаций по вибрационной прочности.  
        - Оценено влияние вибраций на безопасность, надежность и срок службы АКБ.  
        - Соответствие вибрационных параметров требованиям нормативных документов (ГОСТ, ISO, IEC и др.).
        3. Механические воздействия
        - Описаны виды механических воздействий, которым подвергается АКБ (удары, сотрясения, вибрации).  
        - Проведены испытания на ударопрочность и механическую прочность.  
        - Описаны конструктивные меры по повышению механической устойчивости (корпус, крепления, амортизация).  
        - Приведены результаты испытаний и сертификаций по механической прочности.  
        - Оценено влияние механических воздействий на безопасность, надежность и срок службы АКБ.  
        - Соответствие механических параметров требованиям нормативных документов (ГОСТ, ISO, IEC и др.).

        #### Проверка оформления
        Убедитесь, что документ соответствует требованиям оформления:
        - Шрифт, отступы, нумерация разделов
        - Правильные подписи и ссылки на рисунки, таблицы и схемы в тексте

        #### Проверка языка и ясности
        Убедитесь, что язык документа ясен, лаконичен и подходит для целевой аудитории. Проверьте, что все технические термины определены и используются корректно.

        ### Формат ответа
        Для каждой выявленной ошибки укажите:
        - Было: [цитата или описание ошибки]
        - Замечание: [объяснение, почему это ошибка, со ссылкой на стандарт или лучшую практику]
        - Должно быть: [предложение по исправлению]

        ### Примеры
        #### Ошибка в структуре
        - Было: В документе отсутствует раздел «Требования к документации»
        - Замечание: Согласно ГОСТ 15.016-2016, ТЗ должно включать раздел о требованиях к документации, описывающий необходимые документы и их формат
        - Должно быть: Добавить раздел «Требования к документации» с указанием необходимых документов в соответствии с ГОСТ Р 15.301

        #### Ошибка в содержании (неуказанные параметры)
        - Было: Отсутствует информация о токе разряда аккумулятора
        - Замечание: Ток разряда, включая максимальные пиковые токи, обязателен для определения эксплуатационных характеристик (ГОСТ 15.016-2016, раздел технических требований)
        - Должно быть: Указать: «Ток разряда — 120 А, максимальный пиковый ток — 150 А»

        #### Ошибка в ссылках
        - Было: Указан ГОСТ 12345-2000
        - Замечание: ГОСТ 12345-2000 устарел и заменен ГОСТ 12345-2015. Необходимо использовать актуальную версию стандарта
        - Должно быть: Обновить ссылку на ГОСТ 12345-2015

        #### Ошибка в ясности
        - Было: «Аккумулятор должен быть надежным»
        - Замечание: Формулировка неконкретна, не указаны параметры надежности (например, срок службы)
        - Должно быть: «Срок службы аккумулятора не менее 2 лет при соблюдении условий эксплуатации»

        ### Дополнительные замечания
        Если конкретные детали стандарта неизвестны, опирайтесь на общие лучшие практики для технической документации. Приоритет отдавайте ясности, точности и полноте при проверке.

        ### Итоговый результат
        После анализа всего документа составьте полный список выявленных ошибок и предложенных исправлений.

        Текст ТЗ:
        {text}
        """.format(text=text)
        response = await self._llm_request(prompt)
        return response

    async def _llm_request(self, prompt: str) -> str:
        model = CONFIG["llm_model"]
        for attempt in range(CONFIG["retry_attempts"] + 1):
            try:
                async with asyncio.timeout(CONFIG["llm_timeout"]):
                    response = await asyncio.to_thread(
                        g4f.ChatCompletion.create,
                        model=model,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    if isinstance(response, dict):
                        return response.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                    elif isinstance(response, str):
                        return response.strip()
                    else:
                        return "Ответ LLM не распознан."
            except Exception as e:
                if attempt < CONFIG["retry_attempts"]:
                    await asyncio.sleep(CONFIG["retry_interval"])
                else:
                    return f"Не удалось получить ответ от LLM: {str(e)}\n{traceback.format_exc()}"

    async def send_analysis(self, update: Update, analysis: str):
        if len(analysis) <= CONFIG["max_message_length"]:
            await update.message.reply_text(analysis, parse_mode="Markdown")
        else:
            pdf_path = "/tmp/analysis.pdf"
            self.create_pdf(analysis, pdf_path)
            await update.message.reply_text(
                f"Ответ слишком длинный ({len(analysis)} символов), отправляю в виде файла."
            )
            with open(pdf_path, "rb") as f:
                await update.message.reply_document(f)
            os.remove(pdf_path)

    def create_pdf(self, text: str, path: str):
        try:
            font_path = os.path.join(os.path.dirname(__file__), "times.ttf")
            font_bold_path = os.path.join(os.path.dirname(__file__), "timesbd.ttf")
            if not os.path.exists(font_path) or not os.path.exists(font_bold_path):
                raise FileNotFoundError("Шрифты Times New Roman не найдены")
            pdfmetrics.registerFont(TTFont("TimesNewRoman", font_path))
            pdfmetrics.registerFont(TTFont("TimesNewRoman-Bold", font_bold_path))
            c = canvas.Canvas(path, pagesize=letter)
            width, height = letter
            margin = 40
            line_height = 15
            max_width = width - 2 * margin
            c.setFont("TimesNewRoman", 12)
            y = height - margin
            for raw_line in text.split("\n"):
                words = raw_line.split(" ")
                current = ""
                for word in words:
                    test_line = (current + " " + word).strip()
                    if pdfmetrics.stringWidth(test_line, "TimesNewRoman", 12) > max_width:
                        c.drawString(margin, y, current)
                        y -= line_height
                        current = word
                        if y < margin:
                            c.showPage()
                            c.setFont("TimesNewRoman", 12)
                            y = height - margin
                    else:
                        current = test_line
                c.drawString(margin, y, current)
                y -= line_height
                if y < margin:
                    c.showPage()
                    c.setFont("TimesNewRoman", 12)
                    y = height - margin
            c.save()
        except Exception as e:
            raise Exception(f"Ошибка создания PDF: {str(e)}\n{traceback.format_exc()}")

async def main_handler(event, context):
    steps = []
    try:
        steps.append(f"Шаг 1: Получение события (event). Сырые данные event: {json.dumps(event, ensure_ascii=False, indent=2)}")
        
        steps.append("Шаг 2: Получение токена Telegram")
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        steps.append(f"Шаг 3: Проверка токена. Токен получен: {'<скрыт>' if token else 'None'}")
        if not token:
            raise ValueError("Токен Telegram не указан")
        
        steps.append("Шаг 4: Инициализация бота")
        bot = NormalControllerBot(token)
        steps.append("Шаг 5: Бот создан")
        
        steps.append("Шаг 6: Инициализация приложения бота")
        await bot.initialize()
        steps.append("Шаг 7: Приложение бота инициализировано")
        
        steps.append("Шаг 8: Извлечение тела запроса")
        body = event.get('body') or event.get('httpRequest', {}).get('body', '') or json.dumps(event, ensure_ascii=False)
        steps.append(f"Шаг 9: Тело запроса получено. Тип: {type(body)}, содержимое: '{body}'")
        
        if not body:
            raise ValueError(f"Тело запроса отсутствует или пустое: '{body}'")
        steps.append("Шаг 10: Проверка тела пройдена")
        
        steps.append("Шаг 11: Декодирование тела, если байты")
        if isinstance(body, bytes):
            body = body.decode('utf-8', errors='ignore')
            steps.append(f"Шаг 12: Тело декодировано: '{body}'")
        else:
            steps.append(f"Шаг 12: Тело уже строка: '{body}'")
        
        if not body.strip():
            raise ValueError("Пустое тело запроса после декодирования")
        steps.append("Шаг 13: Проверка строки пройдена")
        
        steps.append("Шаг 14: Разбор JSON")
        try:
            update_data = json.loads(body)
            steps.append(f"Шаг 15: JSON разобран: {json.dumps(update_data, ensure_ascii=False, indent=2)}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Не удалось разобрать JSON: {str(e)}")
        
        steps.append("Шаг 16: Проверка JSON")
        if not isinstance(update_data, dict) or not update_data:
            raise ValueError(f"JSON не словарь или пустой: {update_data}")
        steps.append("Шаг 17: JSON валиден")
        
        steps.append("Шаг 18: Создание Update")
        update = Update.de_json(update_data, bot.application.bot)
        if not update:
            raise ValueError(f"Не удалось создать Update: {update_data}")
        steps.append(f"Шаг 19: Update создан: {update}")
        
        steps.append("Шаг 20: Обработка обновления")
        await bot.application.process_update(update)
        steps.append("Шаг 21: Обновление обработано")
        
        steps.append("Шаг 22: Формирование ответа")
        return {'statusCode': 200, 'body': 'OK'}
    
    except Exception as e:
        steps.append(f"Шаг ошибки: Ошибка: {str(e)}")
        return {
            'statusCode': 500,
            'body': f"Ошибка: {str(e)}\nТрассировка:\n{traceback.format_exc()}\n\nШаги:\n" + "\n".join(steps)
        }
"""
Сервис для отправки email-уведомлений
"""
import smtplib
import email.mime.text
import email.mime.multipart
import os
from dotenv import load_dotenv


load_dotenv()

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER',"localhost")
        self.smtp_port = int(os.getenv('SMTP_PORT',25))
        self.smtp_username = os.getenv('SMTP_USERNAME',"user")
        self.smtp_password = os.getenv('SMTP_PASSWORD',"password")


    def send_email(self, to_email, subject, message):
        """
        Отправка email сообщения
        """
        try:
            # Создаем сообщение
            msg = msg = email.mime.multipart.MIMEMultipart()
            msg['From'] = self.smtp_username
            msg['To'] = to_email
            msg['Subject'] = subject

            # Добавляем текст сообщения
            msg.attach(email.mime.text.MIMEText(message, 'plain', 'utf-8'))

            # Создаем соединение с сервером
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()  # Включаем шифрование
            server.login(self.smtp_username, self.smtp_password)

            # Отправляем сообщение
            text = msg.as_string()
            server.sendmail(self.smtp_username, to_email, text)
            server.quit()

            print(f"✅ Email отправлен на {to_email}: {subject}")
            return True

        except Exception as e:
            print(f"❌ Ошибка отправки email на {to_email}: {e}")
            return False

    def send_booking_notification_to_admins(self, booking_data, admin_emails):
        """
        Отправка уведомления администраторам о новой заявке
        """
        subject = "Новая заявка на бронирование аудитории"
        message = f"""
        Поступила новая заявка на бронирование аудитории:

        Аудитория: {booking_data['classroom_number']}
        Дата и время: {booking_data['date']}
        Длительность: {booking_data['duration']} часов
        Описание: {booking_data.get('description', 'Не указано')}
        Пользователь: {booking_data['user_email']}

        Пожалуйста, проверьте заявку в системе и примите решение.
        """

        for admin_email in admin_emails:
            self.send_email(admin_email, subject, message)

    def send_booking_confirmation_to_user(self, user_email, booking_data):
        """
        Отправка подтверждения пользователю о принятии заявки
        """
        subject = "Ваша заявка на бронирование принята"
        message = f"""
        Уважаемый пользователь,

        Ваша заявка на бронирование аудитории успешно создана и принята в рассмотрение.

        Детали заявки:
        Аудитория: {booking_data['classroom_number']}
        Дата и время: {booking_data['date']}
        Длительность: {booking_data['duration']} часов
        Описание: {booking_data.get('description', 'Не указано')}

        Статус: В ожидании решения администратора
        Мы уведомим вас, когда администратор рассмотрит вашу заявку.

        Спасибо за использование нашей системы!
        """

        self.send_email(user_email, subject, message)


# Создаем глобальный экземпляр сервиса
email_service = EmailService()
# email_service.send_email('oleshkasok@gmail.com','oleshkasok@gmail.com','Здарова, сообщение отправлено')

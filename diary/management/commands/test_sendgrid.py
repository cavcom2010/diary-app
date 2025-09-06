"""
Django management command to test SendGrid email integration.
Usage: python manage.py test_sendgrid [email@example.com]
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from diary.email_service import test_sendgrid_connection, send_simple_email


class Command(BaseCommand):
    help = 'Test SendGrid email integration'

    def add_arguments(self, parser):
        parser.add_argument(
            'email',
            nargs='?',
            type=str,
            default=settings.ADMIN_EMAIL,
            help='Email address to send test email to (defaults to ADMIN_EMAIL)'
        )

    def handle(self, *args, **options):
        email = options['email']
        
        self.stdout.write(
            self.style.HTTP_INFO('Testing SendGrid Integration...')
        )
        
        # Check if SendGrid is configured
        if not settings.SENDGRID_API_KEY:
            self.stdout.write(
                self.style.ERROR('❌ SendGrid API key not configured!')
            )
            self.stdout.write(
                'Please set SENDGRID_API_KEY in your .env file'
            )
            return
            
        self.stdout.write(f'📧 Sending test email to: {email}')
        
        # Send test email
        success = send_simple_email(
            subject='🧪 SendGrid Test - My Diary',
            message='''This is a test email from your My Diary application.

If you're receiving this email, it means:
✅ SendGrid is properly configured
✅ Your API key is working
✅ Email delivery is functional

Your My Diary app is ready to send emails!

Test details:
- Sent via SendGrid SMTP
- Django email backend configured
- Templates and settings working

Happy journaling!
The My Diary Team''',
            recipient_list=[email],
            html_message='''
            <h2>🧪 SendGrid Test - My Diary</h2>
            <p>This is a test email from your My Diary application.</p>
            
            <div style="background: #e7f3ff; padding: 15px; border-left: 4px solid #007bff; margin: 15px 0;">
                <h3>✅ Integration Successful!</h3>
                <p>If you're receiving this email, it means:</p>
                <ul>
                    <li>SendGrid is properly configured</li>
                    <li>Your API key is working</li>
                    <li>Email delivery is functional</li>
                </ul>
            </div>
            
            <p><strong>Your My Diary app is ready to send emails!</strong></p>
            
            <h3>Test Details:</h3>
            <ul>
                <li>Sent via SendGrid SMTP</li>
                <li>Django email backend configured</li>
                <li>Templates and settings working</li>
            </ul>
            
            <p>Happy journaling!<br>
            <strong>The My Diary Team</strong></p>
            '''
        )
        
        if success:
            self.stdout.write(
                self.style.SUCCESS('✅ Test email sent successfully!')
            )
            self.stdout.write(
                f'Check the inbox for {email} to confirm delivery.'
            )
        else:
            self.stdout.write(
                self.style.ERROR('❌ Failed to send test email!')
            )
            self.stdout.write(
                'Check your SendGrid configuration and API key.'
            )
            
        # Display configuration info
        self.stdout.write('\n' + self.style.HTTP_INFO('Current Configuration:'))
        self.stdout.write(f'Email Backend: {settings.EMAIL_BACKEND}')
        self.stdout.write(f'SMTP Host: {getattr(settings, "EMAIL_HOST", "Not set")}')
        self.stdout.write(f'SMTP Port: {getattr(settings, "EMAIL_PORT", "Not set")}')
        self.stdout.write(f'TLS Enabled: {getattr(settings, "EMAIL_USE_TLS", "Not set")}')
        self.stdout.write(f'From Email: {settings.DEFAULT_FROM_EMAIL}')
        self.stdout.write(f'Admin Email: {settings.ADMIN_EMAIL}')
        
        api_key_status = "✅ Configured" if settings.SENDGRID_API_KEY else "❌ Not configured"
        self.stdout.write(f'SendGrid API Key: {api_key_status}')
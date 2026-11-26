import io
import json
import os
from datetime import datetime
import matplotlib
matplotlib.use('Agg')  # Prevents Matplotlib from opening its own window
import matplotlib.pyplot as plt

from kivy.app import App
from kivy.core.image import Image as CoreImage
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivy.storage.jsonstore import JsonStore
from kivy.lang import Builder

Builder.load_string('''
<ExpenseRow>:
    canvas.before:
        Color:
            rgba: (0.9, 0.9, 0.9, 1) if self.selected else (1, 1, 1, 1)
        Rectangle:
            pos: self.pos
            size: self.size
    orientation: 'horizontal'
    padding: 10
    height: 60
    Label:
        text: root.category
        size_hint_x: 0.3
        color: 0, 0, 0, 1
    Label:
        text: root.description
        size_hint_x: 0.4
        color: 0, 0, 0, 1
    Label:
        text: ('+' if root.is_income else '-') + str(abs(root.amount)) + ' руб.'
        size_hint_x: 0.3
        color: (0, 0.6, 0, 1) if root.is_income else (0.9, 0.1, 0.1, 1)

<ExpensesRV>:
    viewclass: 'ExpenseRow'
    RecycleBoxLayout:
        default_size: None, dp(60)
        default_size_hint: 1, None
        size_hint_y: None
        height: self.minimum_height
        orientation: 'vertical'

<MainScreen>:
    BoxLayout:
        orientation: 'vertical'
        padding: 20
        spacing: 10
        
        Label:
            text: 'БИЗНЕС-ТРЕКЕР РАСХОДОВ'
            font_size: 24
            bold: True
            color: 0.2, 0.4, 0.8, 1
            size_hint_y: 0.1
            
        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: 0.15
            spacing: 10
            
            Button:
                text: 'Добавить доход'
                on_press: root.show_add_income_popup()
                background_color: 0.4, 0.6, 0.2, 1
            
            Button:
                text: 'Добавить расход'
                on_press: root.show_add_expense_popup()
                background_color: 0.2, 0.6, 0.2, 1
                
            Button:
                text: 'Аналитика (График)'
                on_press: root.show_analytics()
                background_color: 0.3, 0.3, 0.7, 1
                
            Button:
                text: 'Экспорт'
                on_press: root.export_data()
                background_color: 0.7, 0.5, 0.2, 1

            Button:
                text: 'Облако'
                on_press: root.sync_to_cloud()
                background_color: 0.2, 0.5, 0.8, 1
                
        Label:
            text: f'Доходы: {root.total_incomes} руб. | Расходы: {root.total_expenses} руб. | Баланс: {root.total_incomes - root.total_expenses} руб.'
            font_size: 16
            bold: True
            color: (0, 0.6, 0, 1) if (root.total_incomes - root.total_expenses) >= 0 else (1, 0, 0, 1)
            size_hint_y: 0.08
            
        ExpensesRV:
            id: rv
            size_hint_y: 0.67

<AddExpensePopup>:
    size_hint: 0.7, 0.7
    title: 'Добавить новый расход'
    BoxLayout:
        orientation: 'vertical'
        padding: 15
        spacing: 3
        
        Label:
            text: 'Категория:'
            size_hint_y: None
            height: dp(25)
        Spinner:
            id: category_spinner
            text: 'Выберите категорию'
            values: ['Офис', 'Зарплаты', 'Маркетинг', 'Логистика', 'Налоги', 'Прочее']
            size_hint_y: None
            height: dp(25)
            
        Label:
            text: 'Описание:'
            size_hint_y: None
            height: dp(25)
        TextInput:
            id: description_input
            multiline: False
            size_hint_y: None
            height: dp(25)
            
        Label:
            text: 'Сумма (руб.):'
            size_hint_y: None
            height: dp(25)
        TextInput:
            id: amount_input
            multiline: False
            input_filter: 'float'
            size_hint_y: None
            height: dp(25)
            
        BoxLayout:
            orientation: 'horizontal'
            spacing: 10
            size_hint_y: None
            height: dp(45)
            
            Button:
                text: 'Отмена'
                on_press: root.dismiss()
                background_color: 0.8, 0.2, 0.2, 1
                
            Button:
                text: 'Сохранить'
                on_press: root.save_expense()
                background_color: 0.2, 0.6, 0.2, 1

<AddIncomePopup>:
    size_hint: 0.7, 0.7
    title: 'Добавить новый доход'
    BoxLayout:
        orientation: 'vertical'
        padding: 15
        spacing: 3
        
        Label:
            text: 'Категория:'
            size_hint_y: None
            height: dp(25)
        Spinner:
            id: category_spinner
            text: 'Выберите категорию'
            values: ['Дебиторская задолженность', 'Операционная деятельность', 'Проценты по займам']
            size_hint_y: None
            height: dp(25)
            
        Label:
            text: 'Описание:'
            size_hint_y: None
            height: dp(25)
        TextInput:
            id: description_input
            multiline: False
            size_hint_y: None
            height: dp(25)
            
        Label:
            text: 'Сумма (руб.):'
            size_hint_y: None
            height: dp(25)
        TextInput:
            id: amount_input
            multiline: False
            input_filter: 'float'
            size_hint_y: None
            height: dp(25)
            
        BoxLayout:
            orientation: 'horizontal'
            spacing: 10
            size_hint_y: None
            height: dp(45)
            
            Button:
                text: 'Отмена'
                on_press: root.dismiss()
                background_color: 0.8, 0.2, 0.2, 1
                
            Button:
                text: 'Сохранить'
                on_press: root.save_income()
                background_color: 0.2, 0.6, 0.2, 1
''')

class ExpenseRow(RecycleDataViewBehavior, BoxLayout):
    category = StringProperty('')
    description = StringProperty('')
    amount = NumericProperty(0)
    is_income = BooleanProperty(False)
    selected = BooleanProperty(False)
    index = None

    def refresh_view_attrs(self, rv, index, data):
        self.index = index
        return super().refresh_view_attrs(rv, index, data)

class SelectableRecycleBoxLayout(FocusBehavior, LayoutSelectionBehavior, BoxLayout):
    pass

class ExpensesRV(RecycleView):
    pass

class MainScreen(Screen):
    total_expenses = NumericProperty(0)
    total_incomes = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.store_expenses = JsonStore('expenses.json')
        self.store_incomes = JsonStore('incomes.json')
        self.load_all_data()

    def load_all_data(self):
        items = []
        exp_total = 0
        inc_total = 0

        # Загружаем расходы (делаем сумму отрицательной для отображения в списке)
        if os.path.exists('expenses.json'):
            with open('expenses.json', 'r', encoding='utf-8') as f:
                try:
                    for key, exp in json.load(f).items():
                        amt = exp.get('amount', 0)
                        items.append({
                            'category': f"[Расход] {exp.get('category', '')}",
                            'description': exp.get('description', ''),
                            'amount': amt,
                            'is_income': False
                        })
                        exp_total += amt
                except Exception:
                    pass

        # Загружаем доходы (положительная сумма)
        if os.path.exists('incomes.json'):
            with open('incomes.json', 'r', encoding='utf-8') as f:
                try:
                    for key, inc in json.load(f).items():
                        amt = inc.get('amount', 0)
                        items.append({
                            'category': f"[Доход] {inc.get('category', '')}",
                            'description': inc.get('description', ''),
                            'amount': amt,
                            'is_income': True
                        })
                        inc_total += amt
                except Exception:
                    pass

        self.ids.rv.data = items
        self.total_expenses = exp_total
        self.total_incomes = inc_total

    def show_add_expense_popup(self):
        AddExpensePopup(main_screen=self).open()

    def show_add_income_popup(self):
        AddIncomePopup(main_screen=self).open()

    def add_expense(self, category, description, amount):
        try:
            amount = float(amount)
            expense = {
                'category': category,
                'description': description,
                'amount': amount,
                'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            key = f"expense_{datetime.now().timestamp()}"
            self.store_expenses.put(key, **expense)
            self.load_all_data()
        except ValueError:
            self.show_error_popup("Ошибка", "Введите корректную сумму")

    def add_income(self, category, description, amount):
        try:
            amount = float(amount)
            income = {
                'category': category,
                'description': description,
                'amount': amount,
                'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            key = f"income_{datetime.now().timestamp()}"
            self.store_incomes.put(key, **income)
            self.load_all_data()
        except ValueError:
            self.show_error_popup("Ошибка", "Введите корректную сумму")

        incomes = []
        total = 0
        if os.path.exists('incomes.json'):
            with open('incomes.json', 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    for key, income in data.items():
                        incomes.append({
                            'category': income.get('category', ''),
                            'description': income.get('description', ''),
                            'amount': income.get('amount', 0)
                        })
                        total += income.get('amount', 0)
                except Exception:
                    pass
        self.ids.rv.data = incomes
        self.total_incomes = total

    def show_add_expense_popup(self):
        AddExpensePopup(main_screen=self).open()

    def show_add_income_popup(self):
        AddIncomePopup(main_screen=self).open()

    def show_analytics(self):
        """Строит 2 круговые диаграммы (расходы и доходы) и столбчатую диаграмму сравнения"""
        exp_cats = {}
        for key in self.store_expenses.keys():
            item = self.store_expenses.get(key)
            cat = item.get('category', 'Прочее')
            exp_cats[cat] = exp_cats.get(cat, 0) + item.get('amount', 0)

        inc_cats = {}
        for key in self.store_incomes.keys():
            item = self.store_incomes.get(key)
            cat = item.get('category', 'Прочее')
            inc_cats[cat] = inc_cats.get(cat, 0) + item.get('amount', 0)

        if not exp_cats and not inc_cats:
            self.show_error_popup("Нет данных", "Сначала добавьте хотя бы один доход или расход!")
            return

        # Создаём полотно из 3 графиков в один ряд
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(13, 4.5))

        # 1. Круговая диаграмма расходов
        if exp_cats:
            ax1.pie(
                list(exp_cats.values()),
                labels=list(exp_cats.keys()),
                autopct='%1.1f%%',
                startangle=90
            )
            ax1.set_title('Структура расходов')
        else:
            ax1.text(0.5, 0.5, 'Нет расходов', ha='center', va='center')
            ax1.set_title('Структура расходов')
            ax1.axis('off')

        # 2. Круговая диаграмма доходов
        if inc_cats:
            ax2.pie(
                list(inc_cats.values()),
                labels=list(inc_cats.keys()),
                autopct='%1.1f%%',
                startangle=90
            )
            ax2.set_title('Структура доходов')
        else:
            ax2.text(0.5, 0.5, 'Нет доходов', ha='center', va='center')
            ax2.set_title('Структура доходов')
            ax2.axis('off')

        # 3. Столбчатая диаграмма сравнения общих сумм
        totals = [self.total_incomes, self.total_expenses]
        bars = ax3.bar(['Доходы', 'Расходы'], totals, color=['#2E8B57', '#DC143C'])
        ax3.set_title('Доходы vs Расходы')
        ax3.set_ylabel('Сумма, руб.')

        # Подписи точных значений над столбцами
        for bar in bars:
            yval = bar.get_height()
            ax3.text(
                bar.get_x() + bar.get_width() / 2,
                yval,
                f'{yval:.0f}',
                ha='center',
                va='bottom',
                fontweight='bold'
            )

        plt.tight_layout()

        # Конвертируем в текстуру Kivy
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=120)
        plt.close(fig)
        buf.seek(0)
        core_img = CoreImage(buf, ext='png')

        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        chart_widget = Image(texture=core_img.texture, allow_stretch=True, keep_ratio=True)
        close_btn = Button(text='Закрыть', size_hint_y=0.12)
        content.add_widget(chart_widget)
        content.add_widget(close_btn)

        popup = Popup(title='Финансовая аналитика', content=content, size_hint=(0.95, 0.85))
        close_btn.bind(on_press=popup.dismiss)
        popup.open()

    def export_data(self):
        """Экспорт доходов и расходов в один CSV-файл"""
        import csv
        try:
            with open('transactions_export.csv', 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(['Тип', 'Категория', 'Описание', 'Сумма (руб.)', 'Дата'])

                for key in self.store_expenses.keys():
                    item = self.store_expenses.get(key)
                    writer.writerow([
                        'Расход',
                        item.get('category', ''),
                        item.get('description', ''),
                        item.get('amount', 0),
                        item.get('date', '')
                    ])

                for key in self.store_incomes.keys():
                    item = self.store_incomes.get(key)
                    writer.writerow([
                        'Доход',
                        item.get('category', ''),
                        item.get('description', ''),
                        item.get('amount', 0),
                        item.get('date', '')
                    ])

            self.show_error_popup("Успех", "Данные экспортированы в transactions_export.csv")
        except Exception as e:
            self.show_error_popup("Ошибка", str(e))

    def get_api_url(self):
        import os
        if os.path.exists('.env'):
            with open('.env', 'r', encoding='utf-8') as f:
                for line in f:
                    return line
        return "https://jsonplaceholder.typicode.com/posts"

    def sync_to_cloud(self):
        # Синхронизация локальных данных с облачным REST API
        import requests
        
        payload = {
            "expenses": [self.store_expenses.get(k) for k in self.store_expenses.keys()],
            "incomes": [self.store_incomes.get(k) for k in self.store_incomes.keys()],
            "total_balance": self.total_incomes - self.total_expenses,
            "synced_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        api_url = self.get_api_url()

        try:
            response = requests.post(api_url, json=payload, timeout=5)
            if response.status_code in (200, 201):
                server_id = response.json().get('id', 'OK')
                self.show_error_popup(
                    "Облако: Успех",
                    f"Данные синхронизированы!\nID пакета на сервере: {server_id}"
                )
            else:
                self.show_error_popup("Ошибка сервера", f"Код ответа: {response.status_code}")
        except Exception as e:
            self.show_error_popup("Ошибка сети", f"Не удалось подключиться к API:\n{e}")

    def show_error_popup(self, title, message):
        # Показ сообщений
        content = BoxLayout(orientation='vertical', padding=15, spacing=10)
        
        lbl = Label(
            text=message,
            halign='center',
            valign='middle',
            text_size=(self.width, None)
        )

        content.add_widget(lbl)
        
        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.75, 0.45)
        )
        popup.open()
class AddExpensePopup(Popup):
    def __init__(self, main_screen, **kwargs):
        super().__init__(**kwargs)
        self.main_screen = main_screen

    def save_expense(self):
        category = self.ids.category_spinner.text
        description = self.ids.description_input.text
        amount = self.ids.amount_input.text

        if category == 'Выберите категорию':
            self.main_screen.show_error_popup("Ошибка", "Выберите категорию")
            return
        if not description or not amount:
            self.main_screen.show_error_popup("Ошибка", "Заполните все поля")
            return

        self.main_screen.add_expense(category, description, amount)
        self.dismiss()

class AddIncomePopup(Popup):
    def __init__(self, main_screen, **kwargs):
        super().__init__(**kwargs)
        self.main_screen = main_screen

    def save_income(self):
        category = self.ids.category_spinner.text
        description = self.ids.description_input.text
        amount = self.ids.amount_input.text

        if category == 'Выберите категорию':
            self.main_screen.show_error_popup("Ошибка", "Выберите категорию")
            return
        if not description or not amount:
            self.main_screen.show_error_popup("Ошибка", "Заполните все поля")
            return

        self.main_screen.add_income(category, description, amount)
        self.dismiss()

class ExpenseTrackerApp(App):
    def build(self):
        self.title = "Business Expense Tracker"
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        return sm

if __name__ == '__main__':
    ExpenseTrackerApp().run()
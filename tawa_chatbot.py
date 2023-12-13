# # OpenAI Chatbot with TAWA data (v3)
# 
# This TAWA output is from TAR 295, which modelled several single tier FTC changes, one of which was chosen for Budget 22.
# 
# in this version we have reintroduced margin of error for poverty estimates

import io

from aipy.ai import *
import jinja2
import pandas as pd
import panel as pn
import yaml

pn.extension()

MAX_TOKENS = 8000

def load_tawa_file(path):
    values = pd.read_excel(path, sheet_name='Values')
    quantiles = pd.read_excel(path, sheet_name='Quantiles')
    # remove Quantile column
    quantiles.drop(columns='Quantile', inplace=True)
    descriptors = pd.read_excel(path, sheet_name='Descriptors')

    # row append the values and quantiles dataframes and merge with descriptors by Index
    tawa = pd.concat([values, quantiles], axis=0).merge(
        descriptors, on='Index', how='left')

    # sort by Index
    tawa.sort_values(by='Index', inplace=True)
    tawa.drop(columns='Index', inplace=True)
    tawa.reset_index(drop=True, inplace=True)
    return tawa

def update_status(event):
    if details_input.details is not None and data_input.fiscals is not None:
        # ## Prime model
        with open('tawa_priming.jinja2') as f:
            priming_template = jinja2.Template(f.read())
          
        chat.messages = [
            {"role": "system", "content": 'You are wise and helpful.'}]
        chat.add_context(
            priming_template.render(
            tawa_details=details_input.details, fiscals=data_input.fiscals, 
            wnl_wide=data_input.wnl_wide, poverty=data_input.poverty))

        chatbot_status.value = True
        chat_length_indicator.value = chat.get_num_tokens()
        chat_interface.clear()
        chat_interface.send(
            "Ask a question about this TAWA output",
            user="System",
            respond=False,
        )
        download_chat.disabled = False
        clear_chat.disabled = False


class TawaDetailsInput:
    def __init__(self):
        self.details_input = pn.widgets.FileInput(name='Details input: ', accept='.yaml')
        self.details_input.param.watch(self._update_details, 'value')
        self.details_input.param.watch(update_status, 'value')
        self.details = None

    def _update_details(self, event):
        file = io.BytesIO(self.details_input.value) 
        self.details = yaml.load(file, Loader=yaml.FullLoader)


class TawaDataInput:
    def __init__(self):
        self.data_input = pn.widgets.FileInput(name='Data input: ', accept='.xlsx')
        self.data_input.param.watch(self._update_data, 'value')
        self.data_input.param.watch(update_status, 'value')
        self.fiscals = None
        self.wnl_wide = None
        self.poverty = None

    def _update_data(self, event):
        file = io.BytesIO(self.data_input.value) 
        data = load_tawa_file(file)

        data.drop(columns=['Rounding_Rule', 'Population'], inplace=True)
        self.fiscals = data[
            (data.Topic == 'Fiscals') & (data.Variable == 'Disposable_Income')][
                ['Scenario', 'Value']]
        wnl_cols = [
            'Scenario', 'Variable', 'Winner_Loser', 'Eq_DI_Quantile','Value']
        wnl_vars = ['Mean_Weekly_Change', 'Population_In_Category']
        wnl = data[
            (data.Topic == "WnL") & data.Variable.isin(wnl_vars) & 
            (data.WnL_Group == "All Households")][wnl_cols]
        wnl.Eq_DI_Quantile = pd.Categorical(
            wnl.Eq_DI_Quantile, categories=[str(i) for i in range(1, 11)]+['All'], 
            ordered=True)
        wnl.Winner_Loser = pd.Categorical(
            wnl.Winner_Loser, categories=['Winners', 'Losers', 'All'], ordered=True)
        self.wnl_wide = wnl.pivot_table(
            index=['Scenario', 'Eq_DI_Quantile'], 
            columns=['Winner_Loser', 'Variable'], values='Value', 
            aggfunc='first')
        self.wnl_wide.columns = ['_'.join(col).strip() for col in self.wnl_wide.columns.values]
        self.wnl_wide.reset_index(inplace=True)
        self.poverty = data[
            (data.Topic == "Poverty") & (data.Variable == "Change_In_Population_In_Poverty")
            & (data.Population_Type == "Children")][
                ['Scenario', 'Poverty_Type', 'Value', 'Margin_Of_Error']]


details_input = TawaDetailsInput()
data_input = TawaDataInput()
chatbot_status = pn.widgets.BooleanStatus(
    name='Chatbot ready: ', value=False, color='success', width=30, height=30)
chat = Chat()
chat_length_indicator = pn.indicators.LinearGauge(
    name='Chat tokens: ', value=chat.get_num_tokens(), bounds=(0, MAX_TOKENS),
    format='{value}', horizontal=True, align='center', width=70)
download_chat = pn.widgets.FileDownload(
    filename='chat.txt', label='Download chat', button_type='primary', 
    callback=lambda: io.StringIO(chat.format()), disabled=True, height=50)
clear_chat = pn.widgets.Button(
    name='Clear chat', button_type='danger', disabled=True, height=50)
clear_chat.on_click(update_status)


def callback(contents: str, user: str, instance: pn.chat.ChatInterface):
    chat.ask(contents, model="gpt-4")
    message = chat.messages[-1]['content']
    chat_length_indicator.value = chat.get_num_tokens()
    return message
chat_interface = pn.chat.ChatInterface(
    callback=callback, show_rerun=False, show_undo=False, show_clear=False)


template = pn.template.BootstrapTemplate(
    title='TAWA Chatbot',
    sidebar=[
        "Tawa details:", details_input.details_input, 
        "Tawa data: ", data_input.data_input,
        pn.Row("Chatbot ready:", chatbot_status, align=('center', 'center')), 
        chat_length_indicator,
        pn.Row(download_chat, clear_chat)],
    main=[chat_interface],
    logo = "https://huihui/help-me-with/communications/PublishingImages/Pages/The-Treasury%27s-brand-and-logos/TSY%20-%20Logo%20print.png")
template.servable()




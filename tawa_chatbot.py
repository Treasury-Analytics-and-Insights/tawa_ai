# # OpenAI Chatbot with TAWA data (v3)
# 
# This TAWA output is from TAR 295, which modelled several single tier FTC changes, one of which was chosen for Budget 22.
# 
# in this version we have reintroduced margin of error for poverty estimates

from aipy.ai import *
import jinja2
import pandas as pd
import panel as pn
import tiktoken
import yaml

pn.extension()




# ## Load data

# tawa_details contains the tax year and the reform scenario descriptions
with open('tawa_details.yaml') as f:
    tawa_details = yaml.load(f, Loader=yaml.FullLoader)

tawa = pd.read_csv("input/tawa.csv")
tawa.drop(columns=['Name', 'Rounding_Rule', 'Population'], inplace=True)

fiscals = tawa[
    (tawa.Topic == 'Fiscals') & (tawa.Variable == 'Disposable_Income')][
        ['Scenario', 'Value']]

wnl_cols = [
    'Scenario', 'Variable', 'Winner_Loser', 'Eq_DI_Quantile','Value']
wnl_vars = ['Mean_Weekly_Change', 'Population_In_Category']
wnl = tawa[
    (tawa.Topic == "WnL") & tawa.Variable.isin(wnl_vars) & 
    (tawa.WnL_Group == "All Households")][wnl_cols]
wnl.Eq_DI_Quantile = pd.Categorical(
    wnl.Eq_DI_Quantile, categories=[str(i) for i in range(1, 11)]+['All'], 
    ordered=True)
wnl.Winner_Loser = pd.Categorical(
    wnl.Winner_Loser, categories=['Winners', 'Losers', 'All'], ordered=True)
wnl_wide = wnl.pivot_table(index=['Scenario', 'Eq_DI_Quantile'], columns=['Winner_Loser', 'Variable'], values='Value', aggfunc='first')
wnl_wide.columns = ['_'.join(col).strip() for col in wnl_wide.columns.values]
wnl_wide.reset_index(inplace=True)

poverty = tawa[
    (tawa.Topic == "Poverty") & (tawa.Variable == "Change_In_Population_In_Poverty")
    & (tawa.Population_Type == "Children")][
        ['Scenario', 'Poverty_Type', 'Value', 'Margin_Of_Error']]

# ## Prime model
with open('tawa_priming.jinja2') as f:
    priming_template = jinja2.Template(f.read())

chat = Chat()
chat.add_context(
    priming_template.render(
        tawa_details=tawa_details, fiscals=fiscals, wnl_wide=wnl_wide, 
        poverty=poverty))

# Display number of tokens in the context before asking any questions

def num_tokens_from_string(string: str, encoding_name: str) -> int:
    encoding = tiktoken.encoding_for_model(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens


def get_chat_length(chat: Chat, encoding_name: str) -> int:
    content = '\n'.join([m['content'] for m in chat.messages])
    return num_tokens_from_string(content, encoding_name)


def callback(contents: str, user: str, instance: pn.chat.ChatInterface):
    chat.ask(contents, model="gpt-4")
    message = f"{chat.messages[-1]['content']}\nChat tokens: {get_chat_length(chat, 'gpt-4')}"
    return message


chat_interface = pn.chat.ChatInterface(callback=callback)
chat_interface.send(
    "Ask a question about this TAWA output",
    user="System",
    respond=False,
)
chat_interface.servable()




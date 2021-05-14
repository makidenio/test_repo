from dearpygui import core, simple
from os import path
import pandas as pd
import numpy as np

# auxiliary functions

def set_style():
    core.set_style_window_padding(11.00, 7.00)
    core.set_style_frame_padding(4.00, 3.00)
    core.set_style_item_spacing(8.00, 5.00)
    core.set_style_item_inner_spacing(4.00, 4.00)
    core.set_style_touch_extra_padding(0.00, 0.00)
    core.set_style_indent_spacing(19.00)
    core.set_style_scrollbar_size(14.00)
    core.set_style_grab_min_size(10.00)
    core.set_style_window_border_size(0.00)
    core.set_style_child_border_size(0.00)
    core.set_style_popup_border_size(1.00)
    core.set_style_frame_border_size(0.00)
    core.set_style_tab_border_size(0.00)
    core.set_style_window_rounding(0.00)
    core.set_style_child_rounding(0.00)
    core.set_style_frame_rounding(0.00)
    core.set_style_popup_rounding(0.00)
    core.set_style_scrollbar_rounding(0.00)
    core.set_style_grab_rounding(0.00)
    core.set_style_tab_rounding(4.00)
    core.set_style_window_title_align(0.00, 0.50)
    core.set_style_window_menu_button_position(core.mvDir_Left)
    core.set_style_color_button_position(core.mvDir_Right)
    core.set_style_button_text_align(0.50, 0.50)
    core.set_style_selectable_text_align(0.00, 0.00)
    core.set_style_display_safe_area_padding(3.00, 3.00)
    core.set_style_global_alpha(1.00)
    core.set_style_antialiased_lines(True)
    core.set_style_antialiased_fill(True)
    core.set_style_curve_tessellation_tolerance(1.25)
    core.set_style_circle_segment_max_error(1.60)

def column_index(df, query_cols):
    """Helper function to get columns ids."""
    import numpy as np
    cols = df.columns.values
    sidx = np.argsort(cols)
    return sidx[np.searchsorted(cols,query_cols,sorter=sidx)]


# operating functions

def select_file(sender, data):
    core.open_file_dialog(callback=apply_selection, extensions=".csv")

def apply_selection(sender, data):
    file_path = f'{data[0]}\\{data[1]}'
    if path.exists(file_path):
        if core.does_item_exist("File Path",):
            core.set_value("File Path", file_path)
        else:
            core.add_input_text("File Path", default_value=file_path, parent='Main Window', readonly=True)
        options_menu_render(data)
    else:
        core.delete_item("file_not_found")
        core.add_text("file_not_found", parent='Main Window')

def options_menu_render(data):
    core.delete_item('Options Window')
    core.add_child('Options Window', parent='Main Window', horizontal_scrollbar=True)

    # getting path to a file
    df_path = core.get_value("File Path")
    if df_path.endswith('.csv'):
        from datetime import datetime
        df = pd.read_csv(df_path)
        for col in df.columns:
            if any(df[col].astype(str).str.contains(r'\d{4}-\d{2}-\d{2}', regex=True).fillna(False)):
                df[col] = pd.to_datetime(df[col])
                continue
            if (len(df[col].value_counts()) == 2) and (sorted(df[col].value_counts().index.values.tolist()) == [0, 1]):
                df[col] = df[col].fillna(0)
                df[col] = df[col].astype('bool')

        print(df.info())
        print(df)
    else:
        core.delete_item('Table header')
        core.add_text('Not a valid csv file!', parent='Options Window')
        return

    # adding table
    core.add_dummy(name='Padding', height=30, parent='Options Window')
    core.add_text('Table:', parent='Options Window')
    core.add_table(name='Table header', headers=df.columns.tolist(), parent='Options Window')
    core.set_table_data('Table header', df.values.tolist())
    core.add_data('df', df)

    # adding checkboxes
    core.add_dummy(name='Padding2', height=10, parent='Options Window')
    core.add_text('Options', parent='Options Window')
    core.add_checkbox("compute_metrics", parent='Options Window', label='Compute basic metrics (mean, median, std. deviation etc). Opens in a new window')
    core.add_checkbox("missing_values", parent='Options Window', label='Fill in missing values (mean for numeric, mode for nominal data)')

    core.add_checkbox("remove_columns", parent='Options Window', callback=remove_columns_picker, callback_data=df.columns.tolist(), label='Remove columns')
    core.add_indent(name='Rem Indent', parent='Options Window')
    for col in df.columns.tolist():
        core.add_checkbox(col, parent='Options Window', show=False) # columns to remove, shown only after selection
    core.unindent()
    core.add_checkbox('export', parent='Options Window', label='Export to .csv')

    # button
    core.add_button('Commence!', parent='Options Window', callback=perform_operations)

def remove_columns_picker(sender, data):
    """Shows checkboxes for removing columns, which are hidden by default."""
    rem_col_picked = core.get_value("remove_columns")
    for col in data:
        if core.is_item_shown(col) and not rem_col_picked:
            core.configure_item(col, show=False)
        else:
            simple.show_item(col)

def perform_operations(sender, data):
    df = core.get_data('df')

    # get checkbox values
    checkboxes = ['compute_metrics', 'missing_values', 'remove_columns', 'export']
    check_values = dict()
    for checkbox in checkboxes:
        check_values[checkbox] = core.get_value(checkbox)

    # perform different operations based on checkbox values
    if check_values['remove_columns']:
        cols = []
        for col in df.columns.tolist():
            check_val = core.get_value(col)
            if check_val:
                cols.append(col)
        remove_columns(cols)

    if check_values['compute_metrics']:
        compute_metrics()

    if check_values['missing_values']:
        missing_values()

    if check_values['export']:
        export()


def remove_columns(columns):
    df = core.get_data('df')
    columns_int = column_index(df, columns)
    for col in columns_int:
        core.delete_column("Table header", col)

    df = df.drop(columns, axis=1)
    core.delete_data('df')
    core.add_data('df', df)

def missing_values():
    df = core.get_data('df')
    print(df.dtypes.loc['first_name'] == 'object')
    cols_to_fill = df.dtypes.loc[df.dtypes.isin(['object', 'float64', 'int64'])]
    print(cols_to_fill)
    for col in cols_to_fill.index:
        if pd.api.types.is_string_dtype(cols_to_fill.loc[col]):
            mode = df[col].value_counts().idxmax()
            df[col] = df[col].fillna(mode)

        if pd.api.types.is_numeric_dtype(cols_to_fill.loc[col]):
            mean = df[col].mean()
            df[col] = df[col].fillna(mean)
    
    core.set_table_data('Table header', df.values.tolist())

    core.delete_data('df')
    core.add_data('df', df)

def compute_metrics():
    core.delete_item('Metrics')
    core.add_window('Metrics', autosize=True, x_pos=50, y_pos=50)
    df = core.get_data('df').describe().reset_index()
    df = df.rename({'index': 'METRICS'}, axis=1)

    core.add_table(name='Metrics table', headers=df.columns.tolist())
    core.set_table_data('Metrics table', df.values.tolist())
    core.move_item_up('Metrics')

def export():
    df = core.get_data('df')
    df.to_csv('export.csv', index=False)
    core.add_text('Exported to /export.csv : -)', parent='Options Window')



with simple.window('Main Window', width=700, height=700, x_pos=0, y_pos=0, no_resize=True, no_move=True, no_close=True, no_title_bar=True):
    set_style()
    core.add_additional_font('Montserrat-Regular.ttf', 16)
    core.add_text('Pick a file:')
    core.add_button("Select file...", callback=select_file)

core.set_main_window_size(height=700, width=700)
core.set_main_window_title('Ploziol statistics v0.1')
core.set_main_window_resizable(False)

core.start_dearpygui()
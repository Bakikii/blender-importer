import os.path as op
import os
import time

MAX_TIME_TO_WAIT_FOR_FILES = 60  # minute
TIME_TO_WAIT_FOR_FINALIZED = 1
PIAL_VIEW_DISTANCE = 18 #15
INFLATED_VIEW_DISTANCE = 25 #21


def run(mmvt, cb_min=None, cb_max=None, threshold=None, overwrite=True):
    if cb_min is None:
        cb_min = 2
    if cb_max is None:
        cb_max = 6
    if threshold is None:
        threshold = 2
    inflating_ratio = mmvt.appearance.get_inflated_ratio()
    view_distance = mmvt.render.get_view_distance()
    subcorticals_are_hiding = mmvt.show_hide.subcorticals_are_hiding()

    # Set a new output folder
    report = mmvt.reports.get_report_fields()
    print('Setup fMRI report, where task="{}", patient name="{}", date="{}" and MRN="{}"'.format(
        report.task_name, report.patient_name, report.date, report.mrn_number))
    mmvt.reports.set_report_name('fMRI report')
    if report.task_name == '':
        report.task_name = 'unknown'
    new_output_fol = op.join(mmvt.utils.get_user_fol(), 'reports', report.task_name.replace(' ', '_'))
    mmvt.utils.make_dir(new_output_fol)
    mmvt.render.set_output_path(new_output_fol)
    mmvt.render.set_resolution_percentage(50)

    # Get the report necessary files. If exist, move them to a backup folder
    report_files = [op.join(new_output_fol, f) for f in mmvt.get_report_files()]
    if overwrite:
        if any(op.isfile(f) for f in report_files):
            mmvt.utils.make_dir(op.join(new_output_fol, 'backup'))
        for f in report_files:
            mmvt.utils.move_file(f, op.join(new_output_fol, 'backup'))

    # Set the colorbar
    mmvt.colorbar.set_colorbar_min_max(cb_min, cb_max)
    mmvt.colorbar.set_colormap('RdOrYl')
    mmvt.colorbar.set_colorbar_title('')
    mmvt.colorbar.set_cb_ticks_num(3)
    mmvt.colorbar.set_cb_ticks_font_size(16)
    mmvt.colorbar.lock_colorbar_values()

    # Change to pial surface, show both hemis and hide the subcorticals
    mmvt.appearance.show_pial()
    mmvt.show_hide.show_hemis()

    # Set a threshold and plot the fmri activity
    mmvt.coloring.set_lower_threshold(threshold)
    mmvt.coloring.set_use_abs_threshold(False)  # No negative values
    mmvt.coloring.plot_fmri()

    # Save figures for pial and inflated without the subcorticals
    if overwrite:
        mmvt.render.save_views_with_cb()
        mmvt.render.set_save_split_views()
        mmvt.show_hide.hide_subcorticals()
        views = [mmvt.ROT_SAGITTAL_LEFT, mmvt.ROT_SAGITTAL_RIGHT, mmvt.ROT_AXIAL_INFERIOR]
        mmvt.render.set_view_distance(PIAL_VIEW_DISTANCE)
        mmvt.render.save_all_views(views)
        mmvt.appearance.show_inflated()
        mmvt.render.set_view_distance(INFLATED_VIEW_DISTANCE)
        mmvt.render.save_all_views(views)

        # Wait until all the files are created
        now = time.time()
        while not all([op.isfile(f) for f in report_files]):
            time.sleep(0.1)
            if time.time() - now > MAX_TIME_TO_WAIT_FOR_FILES:
                print('Not all the files exist!')
                return

    # Wait for all the figures to get finalized
    time.sleep(TIME_TO_WAIT_FOR_FINALIZED)
    #  Create the pdf report
    mmvt.reports.create_report()
    # Remove temp colorbar figure
    os.remove(mmvt.colorbar.get_colorbar_figure_fname())

    # Return to prev vis
    mmvt.appearance.set_inflated_ratio(inflating_ratio)
    mmvt.render.set_view_distance(view_distance)
    if subcorticals_are_hiding:
        mmvt.show_hide.show_subcorticals()
    else:
        mmvt.show_hide.show_subcorticals()
    mmvt.utils.center_view()

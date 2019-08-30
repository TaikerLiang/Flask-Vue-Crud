from crawler.core_carrier.items import MblItem, VesselItem, LocationItem, ContainerItem, ContainerStatusItem


class Verifier:

    def __init__(self, mbl_no):
        self.mbl_no = mbl_no

    def verify(self, result):

        assert result[0] == ContainerItem(
         container_no='CAIU7479659',
         last_free_day='Gated-out',
         mt_location='M&N EQUIPMENT SERVICES ( EMPTIES ONLY) (MINNEAPOLIS, MN)',
         det_free_time_exp_date='09-May-2019',
         por_etd=None,
         pol_eta=None,
         final_dest_eta=None,
         ready_for_pick_up='Already picked up',
        )

class Second_Model:

    def sec_to_time(self, sec):
        try:
            m, s = divmod(sec, 60)
            h, m = divmod(m, 60)
            return "%02d:%02d:%02d" % (h, m, s)
        except TypeError as e:
            print("sec_to_time", e)
            return '0'

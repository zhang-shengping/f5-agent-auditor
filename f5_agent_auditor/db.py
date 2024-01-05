# -*- coding: utf-8 -*-

from f5_agent_auditor import options
from sqlalchemy import create_engine


conf = options.cfg.CONF


def init():
    engine = create_engine(conf.database.connection)
    conn = engine.connect()
    return conn


def to_dict(row):
    if row:
        return dict(row.items())
    return {}


def to_pytype(string):
    if string:
        return eval(string)
    return ""


class LbaasDBResource(object):

    def __init__(self):
        self.conn = init()

    def fetchall(self, text):
        return self.conn.execute(text).fetchall()

    def first(self, text):
        return self.conn.execute(text).first()

    def get_bindings(self):
        rows = self.fetchall("SELECT * FROM lbaas_loadbalanceragentbindings")
        ret = []

        if not rows:
            return ret

        ret = [to_dict(r) for r in rows]

        return ret

    def get_devices(self):
        rows = self.fetchall("SELECT * FROM lbaas_devices")
        ret = []

        if not rows:
            return ret

        for r in rows:
            r = to_dict(r)
            r['device_info'] = to_pytype(r['device_info'])
            r['provisioning_status'] = to_pytype(r['provisioning_status'])
            ret.append(r)

        return ret

    def get_device_group_by_id(self, dev_id):
        ret = self.first('SELECT * FROM lbaas_devices WHERE id="%s"' % dev_id)

        if not ret:
            return ret

        ret = dict(ret)
        ret['device_info'] = to_pytype(ret['device_info'])
        ret['provisioning_status'] = to_pytype(ret['provisioning_status'])

        return ret

    def get_device_group_by_ids(self, ids=[]):
        ids = ','.join('"{0}"'.format(i) for i in ids)
        rows = self.fetchall(
            'SELECT * FROM lbaas_devices WHERE id IN (%s)' % ids)
        ret = []

        if not rows:
            return ret

        for r in rows:
            r = to_dict(r)
            r['device_info'] = to_pytype(r['device_info'])
            r['provisioning_status'] = to_pytype(r['provisioning_status'])
            ret.append(r)

        return ret

    def get_devices_by_group_id(self, group_id):
        rows = self.fetchall(
            'SELECT * FROM lbaas_device_members WHERE device_id="%s"' %
            group_id)

        ret = []

        if not rows:
            return ret

        for r in rows:
            r = to_dict(r)
            r['device_info'] = to_pytype(r['device_info'])
            r['operating_status'] = to_pytype(r['operating_status'])
            r['last_error'] = to_pytype(r['last_error'])
            ret.append(r)

        return ret

    def get_agent_by_id(self, agt_id):
        ret = self.first('SELECT * FROM agents WHERE id="%s"' % agt_id)

        if not ret:
            return ret

        ret = dict(ret)
        ret['configurations'] = to_pytype(ret['configurations'])

        return ret

    def get_agent_by_ids(self, ids=[]):
        ids = ','.join('"{0}"'.format(i) for i in ids)
        rows = self.fetchall(
            'SELECT * FROM agents WHERE id IN (%s)' % ids)
        ret = []

        if not rows:
            return ret

        for r in rows:
            r = to_dict(r)
            r['configurations'] = to_pytype(r['configurations'])
            ret.append(r)

        return ret

    def get_loadbalancer_by_id(self, lb_id):
        ret = self.first(
            'SELECT * FROM lbaas_loadbalancers WHERE id="%s"' % lb_id)

        if not ret:
            return ret

        ret = dict(ret)

        return ret

    def get_loadbalancer_by_ids(self, ids=[]):
        ids = ','.join('"{0}"'.format(i) for i in ids)
        rows = self.fetchall(
            'SELECT * FROM lbaas_loadbalancers WHERE id IN (%s)' % ids)
        ret = []

        if not rows:
            return ret
        ret = [dict(r) for r in rows]

        return ret

    def get_loadbalancers_by_project(self, project_id):
        rows = self.fetchall(
            'SELECT * FROM lbaas_loadbalancers WHERE project_id="%s"' %
            project_id)
        ret = []

        if not rows:
            return ret
        ret = [dict(r) for r in rows]

        return ret

    def get_listeners_by_project(self, project_id):
        rows = self.fetchall(
            'SELECT * FROM lbaas_listeners WHERE project_id="%s"' %
            project_id)
        ret = []

        if not rows:
            return ret
        ret = [dict(r) for r in rows]

        return ret

    def get_pools_by_project(self, project_id):
        rows = self.fetchall(
            'SELECT * FROM lbaas_pools WHERE project_id="%s"' %
            project_id)
        ret = []

        if not rows:
            return ret
        ret = [dict(r) for r in rows]

        return ret

    def get_members_by_pool(self, pool_id):
        rows = self.fetchall(
            'SELECT * FROM lbaas_members WHERE pool_id="%s"' %
            pool_id)
        ret = []

        if not rows:
            return ret
        ret = [dict(r) for r in rows]

        return ret

    def get_monitors_by_id(self, mn_id):
        rows = self.fetchall(
            'SELECT * FROM lbaas_healthmonitors WHERE id="%s"' %
            mn_id)
        ret = []

        if not rows:
            return ret
        ret = [dict(r) for r in rows]

        return ret

    def get_subnet_by_id(self, subnet_id):
        ret = None
        ret = self.first('SELECT * FROM subnets WHERE id="%s"' % subnet_id)

        if not ret:
            return ret

        ret = dict(ret)

        return ret

    def get_net_by_id(self, net_id):
        ret = None
        ret = self.first('SELECT * FROM networks WHERE id="%s"' % net_id)

        if not ret:
            return ret

        ret = dict(ret)

        return ret

    def get_net_by_name(self, net_name):
        ret = None
        ret = self.first('SELECT * FROM networks WHERE name="%s"' % net_name)

        if not ret:
            return ret

        ret = dict(ret)

        return ret

    def get_subnet_by_netid(self, net_id):
        rows = self.fetchall(
            'SELECT * FROM subnets WHERE network_id="%s"' % net_id)
        ret = []

        if not rows:
            return ret
        ret = [dict(r) for r in rows]

        return ret

    def get_segments_by_net_id(self, net_id):
        rows = self.fetchall(
            'SELECT * FROM networksegments WHERE network_id="%s"' % net_id)
        ret = []

        if not rows:
            return ret
        ret = [dict(r) for r in rows]

        return ret

    def get_listeners_by_lbid(self, lb_id):
        rows = self.fetchall(
            'SELECT * FROM lbaas_listeners WHERE loadbalancer_id="%s"' % lb_id)
        ret = []

        if not rows:
            return ret
        ret = [dict(r) for r in rows]

        return ret

    def get_pools_by_lbid(self, lb_id):
        rows = self.fetchall(
            'SELECT * FROM lbaas_pools WHERE loadbalancer_id="%s"' % lb_id)
        ret = []

        if not rows:
            return ret
        ret = [dict(r) for r in rows]

        return ret

    def get_members_by_plid(self, pool_id):
        rows = self.fetchall('SELECT * FROM lbaas_members WHERE pool_id="%s"' %
                             pool_id)
        ret = []

        if not rows:
            return ret
        ret = [dict(r) for r in rows]

        return ret

    def get_policies_by_lsid(self, listener_id):
        rows = self.fetchall(
            'SELECT * FROM lbaas_l7policies WHERE listener_id="%s"' %
            listener_id)
        ret = []

        if not rows:
            return ret
        ret = [dict(r) for r in rows]

        return ret

    def get_l7rules_by_polid(self, policy_id):
        rows = self.fetchall(
            'SELECT * FROM lbaas_l7rules WHERE l7policy_id="%s"' %
            policy_id)
        ret = []

        if not rows:
            return ret
        ret = [dict(r) for r in rows]

        return ret

    def _format_filters(self, filters):
        comb = ""
        tmp = []

        for k, v in filters.items():
            tmp.append('%s="%s"' % (k, v))

        if tmp:
            flt = " AND ".join(tmp)
            comb = "WHERE " + flt

        return comb

    def try_to_find(self, table, filters):
        table = "lbaas_" + table

        if filters:
            where_comb = self._format_filters(filters)
            stat = 'SELECT * FROM ' + table + ' ' + where_comb
            row = self.first(stat)
            if row:
                return dict(row)


if __name__ == "__main__":
    conf.connection = "mysql+pymysql://neutron:c888221d9aec4d20@10.145.74.159/neutron"
    resource = LbaasDBResource()
    resource.get_device_by_id("3b76a64c-2269-47a3-adaf-5bbcecf83156")
    resource.get_agent_by_id("c902e259-e52b-44b6-89e1-61ea9830c7d8")
    resource.get_device_by_ids(["3b76a64c-2269-47a3-adaf-5bbcecf83156"])

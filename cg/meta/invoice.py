# -*- coding: utf-8 -*-
from typing import List

from cg.apps import lims, invoice
from cg.store import Store, models
from cg.server.ext import lims as genologics_lims


class InvoiceAPI():

    def __init__(self, db: Store, lims_api: lims.LimsAPI, invoice_obj: models.Invoice):
        self.db = db
        self.lims_api = lims_api
        self.log = []
        self.invoice_obj = invoice_obj
        self.customer_obj = invoice_obj.customer

    def prepare_contact_info(self, costcenter):
        msg = f'Could not open/generate invoice. Contact information missing in database for ' \
            f'customer {self.customer_obj.internal_id}. See log files.'
        if costcenter.lower() == 'kth':
            customer = self.db.customer('cust999')
        else:
            customer = self.customer_obj
        user = customer.invoice_contact

        if not user:
            self.log.append(msg)
            return None

        contact = {
            'name': user.name,
            'email': user.email,
            'customer_name': customer.name,
            'reference': customer.invoice_reference,
            'address': customer.invoice_address,
        }

        if None in contact.values():
            self.log.append(msg)
            return None
        return contact

    def prepare(self, costcenter: str) -> dict:
        """Get information about an invoice to generate Excel report."""

        records = []
        pooled_samples = []
        record_type = ''
        if self.invoice_obj.pools:
            record_type = 'Pool'
            for pool in self.invoice_obj.pools:
                pooled_samples += genologics_lims.samples_in_pools(pool.name, pool.ticket_number)
                record = self.prepare_record(
                    costcenter=costcenter.lower(),
                    discount=self.invoice_obj.discount,
                    record=pool)
                if record:
                    records.append(record)
                else:
                    return None
        elif self.invoice_obj.samples:
            record_type = 'Prov'
            for sample in self.invoice_obj.samples:
                record = self.prepare_record(
                    costcenter=costcenter.lower(),
                    discount=self.invoice_obj.discount,
                    record=sample)
                if record:
                    records.append(record)
                else:
                    return None

        customer_obj = self.invoice_obj.customer
        contact = self.prepare_contact_info(costcenter)
        if not contact:
            return None
        return {
            'costcenter': costcenter,
            'project_number': getattr(customer_obj, f"project_account_{costcenter.lower()}"),
            'customer_id': customer_obj.internal_id,
            'customer_name': customer_obj.name,
            'agreement': customer_obj.agreement_registration,
            'invoice_id': self.invoice_obj.id,
            'contact': contact,
            'records': records,
            'pooled_samples': pooled_samples,
            'record_type': record_type
        }

    def prepare_record(self, costcenter: str, discount: int, record: models.Sample):
        """Get information to invoice a sample."""
        try:
            tag = record.application_version.application.tag
            version = str(record.application_version.version)
            percent_kth = record.application_version.application.percent_kth
            discounted_price = self.get_price(discount, record)
        except:
            self.log.append(f'Application tag/version semms to be missing for sample {record.id}.')
            return None

        if type(record)==models.Pool:
            lims_id = None
            priority = 'research'
        elif type(record)==models.Sample:
            lims_id = record.internal_id
            priority = record.priority_human

        if discounted_price:
            try:
                if costcenter == 'kth':
                    split_factor = percent_kth / 100
                else:
                    split_factor = (100 - percent_kth) / 100
                price = round(discounted_price * split_factor, 1)
            except:
                self.log.append(f'Could not calculate price for samples with application '
                                f'tag/version: {tag}/{version}. Missing %KTH')
                return None
        else:
            self.log.append(
                f'Could not get price for samples with application tag/version: {tag}/{version}.')
            return None

        return {
            'name': record.name,
            'lims_id': lims_id,
            'id': record.id,
            'application_tag': record.application_version.application.tag,
            'project': f"{record.order or 'NA'} ({record.ticket_number or 'NA'})",
            'date': record.received_at.date() if record.received_at else '',
            'price': price,
            'priority': priority
        }

    def get_price(self, discount: int, record: models.Sample):
        """Get discount price for a sample."""
        if type(record)==models.Pool:
            priority='research'
        elif type(record)==models.Sample:
            priority = record.priority_human

        full_price = getattr(record.application_version, f"price_{priority}")
        if not discount:
            discount = 0
        discount_factor = float(100 - discount) / 100
        if not full_price:
            return None
        return full_price * discount_factor

    def total_price(self) -> float:
        discount = self.invoice_obj.discount
        total_price = 0
        if self.invoice_obj.pools:
            for record in self.invoice_obj.pools:
                if self.get_price(discount, record):
                    total_price += self.get_price(discount, record)
                else:
                    return None
        elif self.invoice_obj.samples:
            for record in self.invoice_obj.samples:
                if self.get_price(discount, record):
                    total_price += self.get_price(discount, record)
                else:
                    return None
        return total_price

import rules

from .utils import in_editable_period


# Business rules

@rules.predicate
def is_business_owner(user, business):
    return business.user == user

rules.add_perm('cashup.view_business', is_business_owner)
rules.add_perm('cashup.change_business', is_business_owner)

# Outlet rules

@rules.predicate
def is_owner_of(user, outlet):
    return outlet.business.user == user

@rules.predicate
def is_staff_of(user, outlet):
    return outlet.staff.filter(pk=user.pk).exists()

@rules.predicate
def is_business_owner(user):
    return hasattr(user, 'business')

@rules.predicate
def is_outlet_manager(user, outlet):
    return outlet.outletstaff_set.filter(user=user, is_manager=True).exists()

is_owner_or_staff_of = is_owner_of | is_staff_of

rules.add_perm('cashup.change_outlet', is_owner_of | is_outlet_manager)
rules.add_perm('cashup.view_outlet', is_owner_or_staff_of)
rules.add_perm('cashup.create_outlet', is_business_owner)

# TillClosure rules

@rules.predicate
def closed_by(user, tillcashup):
    return tillcashup.closed_by == user

@rules.predicate
def is_editable(user, tillcashup):
    return in_editable_period(tillcashup.close_time)

@rules.predicate
def is_owner_of_outlet(user, tillcashup):
    return tillcashup.outlet.business.user == user

@rules.predicate
def is_staff_of_outlet(user, tillcashup):
    return tillcashup.outlet.staff.filter(pk=user.pk).exists()

@rules.predicate
def is_manager_of_outlet(user, outlet):
    return tillcashup.outlet.outletstaff_set.filter(
        user=user, is_manager=True).exists()

is_staff_and_is_editable = is_staff_of_outlet & is_editable

rules.add_perm('cashup.view_tillclosures_for_outlet',
    is_staff_of | is_owner_of)

rules.add_perm('cashup.create_tillclosure_for_outlet',
    is_staff_of | is_owner_of)

rules.add_perm('cashup.view_tillclosure_new',
    is_staff_of_outlet | is_owner_of_outlet)

# TODO: do I need this??
rules.add_rule('cashup.change_tillclosure',
    is_staff_and_is_editable | is_owner_of_outlet)

rules.add_perm('cashup.change_tillclosure',
    is_staff_and_is_editable | is_manager_of_outlet | is_owner_of_outlet)

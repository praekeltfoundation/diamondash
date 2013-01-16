def stub_fn(targetobj, targetfn, stubfn):
    original = getattr(targetobj, targetfn)
    setattr(targetobj, targetfn, stubfn)

    stubfn.targetobj = targetobj
    stubfn.targetfn = targetfn
    stubfn.original = original


def restore_from_stub(stubfn):
    setattr(stubfn.targetobj, stubfn.targetfn, stubfn.original)


def stub_classmethod(targetobj, targetfn, stubfn):
    original = getattr(targetobj, targetfn)
    setattr(targetobj, targetfn, classmethod(stubfn))

    stubfn.targetobj = targetobj
    stubfn.targetfn = targetfn
    stubfn.original = original

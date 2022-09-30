def show_tag_count(ehd, show=False):
    visits = [(m, len(ehd.get_visits(m))) for m in ehd.mice]
    visits = sorted(visits, key=lambda x: x[1], reverse=True)

    if show:
        for m, c in visits:
            print("%s: %d" % (m, c))

    return dict(visits)

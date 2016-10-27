def get_line(lines, starting):
    """ Reads lines until it hits the starting string. Note that the read
    line is being stripped, meaning that putting whitespace in the starting
    string would be redundant.

    Arguments:
        lines - File like object. A file like (or url) object which can be iterated through
        for lines.
        starting - string. The string which the line should start with.
    Returns:
        The line which starts with the line. If not available it will return
        an empty string.
    """
    for line in lines:
        line = line.strip()
        if line.startswith(starting):
            return line[len(starting):].lstrip()
    return ""

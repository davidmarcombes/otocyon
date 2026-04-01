from otocyon.framework import strategy, on_data


def test_on_data_tagging():
    @strategy("TagTest")
    class TagTestStrategy:
        @on_data(frequency="1m")
        def my_handler(self, instruments, ctx):
            return "processed"

    # Instantiate and find the marked method
    strat = TagTestStrategy()
    handler = strat.my_handler

    # Check if our hidden attributes exist
    assert getattr(handler, "_is_data_handler") is True
    assert getattr(handler, "_frequency") == "1m"
    # Ensure functools.wraps kept the original function name
    assert handler.__name__ == "my_handler"

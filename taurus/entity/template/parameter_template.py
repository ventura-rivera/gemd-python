from taurus.entity.template.attribute_template import AttributeTemplate
from taurus.entity.attribute.parameter import Parameter


class ParameterTemplate(AttributeTemplate):
    """A template for the parameter attribute."""

    typ = "parameter_template"

    def __call__(
        self, name=None, template=None, origin="unknown", value=None, notes=None, file_links=None
    ):
        """Produces a parameter that is linked to this parameter template."""

        if not name:  # inherit name from the template by default
            name = self.name

        if not template:  # link the parameter to this template by default
            template = self

        return Parameter(
            name=name,
            template=template,
            origin=origin,
            value=value,
            notes=notes,
            file_links=file_links,
        )

from inertia.test import InertiaTestCase


class HomeViewTests(InertiaTestCase):
    def test_home_renders_the_home_component(self):
        self.client.get("/")

        self.assertComponentUsed("Home")
        self.assertIncludesProps({"appName": "SIMTELE Risk"})

    def test_optional_prop_is_absent_on_the_first_load(self):
        self.client.get("/")

        self.assertNotIn("slowFact", self.props())

    def test_partial_reload_returns_only_requested_props_plus_always(self):
        self.inertia.get(
            "/",
            HTTP_X_INERTIA_PARTIAL_COMPONENT="Home",
            HTTP_X_INERTIA_PARTIAL_DATA="slowFact",
        )

        page = self.inertia.last_response.json()
        # `appName` is wrapped in always(), so it is present even though the
        # client only asked for `slowFact`.
        self.assertEqual(set(page["props"]), {"appName", "slowFact"})
        self.assertIn("body", page["props"]["slowFact"])

    def test_once_prop_metadata_is_exposed(self):
        self.client.get("/")

        self.assertEqual(self.once_props()["server-info"]["prop"], "serverInfo")

    def test_greet_flashes_a_django_message(self):
        response = self.client.post("/greet/", {"name": "Ada"})

        self.assertRedirects(response, "/")
        flash = self.page()["flash"]["messages"]
        self.assertEqual(flash[0]["level"], "success")
        self.assertIn("Ada", flash[0]["message"])

    def test_flash_message_is_consumed_after_one_response(self):
        self.client.post("/greet/", {"name": "Ada"})
        self.client.get("/")  # first response receives the flash
        self.client.get("/")  # second response must not

        self.assertNotIn("flash", self.page())

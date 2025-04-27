"""Main client and locator logic for the Terminator SDK."""

import requests
import json
import logging
import time
from typing import List, Optional, Dict, Any, Type, TypeVar
from dataclasses import asdict

from .exceptions import ApiError, ConnectionError
from .models import (
    BasicResponse, BooleanResponse, TextResponse, ElementResponse, ElementsResponse,
    ClickResponse, AttributesResponse, BoundsResponse, ChainedRequest,
    TypeTextRequest, GetTextRequest, PressKeyRequest, OpenApplicationRequest,
    OpenUrlRequest, ExpectRequest, ExpectTextRequest
)

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "http://127.0.0.1:3000"

# Generic type variable for response models
T = TypeVar('T')

class DesktopUseClient:
    """Client for interacting with the Terminator desktop automation server."""

    def __init__(self, base_url: str = DEFAULT_BASE_URL):
        """
        Initializes the client.

        Args:
            base_url: The base URL of the Terminator server (e.g., http://127.0.0.1:3000).
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        logger.info(f"DesktopUseClient initialized for server at {self.base_url}")

    def _make_request(self, endpoint: str, payload: Any, response_model: Type[T]) -> T:
        """Internal helper to make POST requests and handle responses."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        # Convert dataclass payload to dict, handle non-dataclass payloads
        if hasattr(payload, '__dataclass_fields__'):
             payload_dict = asdict(payload, dict_factory=lambda x: {k: v for (k, v) in x if v is not None})
        elif isinstance(payload, dict):
            payload_dict = payload
        else:
            raise TypeError("Payload must be a dataclass instance or a dictionary")

        json_payload = json.dumps(payload_dict)
        logger.debug(f"Sending POST to {url} with payload: {json_payload}")

        try:
            response = self.session.post(url, data=json_payload)
            logger.debug(f"Response Status: {response.status_code}")
            logger.debug(f"Response Data: {response.text[:500]}...") # Log truncated response

            if 200 <= response.status_code < 300:
                try:
                    if not response.content or response.status_code == 204:
                        # Handle No Content or empty successful response
                        # Return default instance if possible, or a basic message
                        if response_model is BasicResponse:
                            return BasicResponse(message="Operation successful") # type: ignore
                        try:
                            # Try creating a default instance (works for some dataclasses)
                             return response_model()
                        except TypeError:
                             # Fallback if default construction fails
                             logger.warning(f"Received empty success response for {response_model.__name__}, returning default BasicResponse")
                             return BasicResponse(message="Operation successful (empty response)") # type: ignore

                    data = response.json()
                    # Use dictionary unpacking to create the dataclass instance
                    return response_model(**data)
                except (json.JSONDecodeError, TypeError) as e:
                    logger.error(f"Failed to decode JSON or create response model {response_model.__name__}: {e}", exc_info=True)
                    raise ApiError(f"Invalid JSON response or model mismatch: {e}", response.status_code)
            else:
                # Attempt to parse error message from server
                try:
                    error_data = response.json()
                    error_message = error_data.get('message', response.text)
                except json.JSONDecodeError:
                    error_message = response.text
                logger.error(f"API Error ({response.status_code}): {error_message}")
                raise ApiError(error_message, response.status_code)

        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection Error connecting to {url}: {e}", exc_info=True)
            raise ConnectionError(f"Could not connect to Terminator server at {url}. Is it running? Details: {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}", exc_info=True)
            raise ApiError(f"An unexpected request error occurred: {e}")

    def locator(self, selector: str) -> 'Locator':
        """
        Creates a new Locator instance starting from the root.

        Args:
            selector: The initial selector string.

        Returns:
            A new Locator instance.
        """
        if not isinstance(selector, str) or not selector:
            raise ValueError("Initial selector must be a non-empty string.")
        return Locator(self, [selector])

    def open_application(self, app_name: str) -> BasicResponse:
        """
        Opens an application by its name or path.

        Args:
            app_name: The name or path of the application.

        Returns:
            BasicResponse indicating success.
        """
        payload = OpenApplicationRequest(app_name=app_name)
        return self._make_request("/open_application", payload, BasicResponse)

    def open_url(self, url: str, browser: Optional[str] = None) -> BasicResponse:
        """
        Opens a URL, optionally in a specific browser.

        Args:
            url: The URL to open.
            browser: Optional browser name/path.

        Returns:
            BasicResponse indicating success.
        """
        payload = OpenUrlRequest(url=url, browser=browser)
        return self._make_request("/open_url", payload, BasicResponse)


class Locator:
    """Represents a UI element locator, allowing chained selections and actions."""

    def __init__(self, client: DesktopUseClient, selector_chain: List[str]):
        """Internal constructor. Use client.locator() to create instances."""
        self._client = client
        self._selector_chain = selector_chain

    def locator(self, selector: str) -> 'Locator':
        """
        Creates a new Locator scoped to the current one.

        Args:
            selector: The selector to append to the chain.

        Returns:
            A new Locator instance.
        """
        if not isinstance(selector, str) or not selector:
            raise ValueError("Nested selector must be a non-empty string.")
        new_chain = self._selector_chain + [selector]
        return Locator(self._client, new_chain)

    # --- Action Methods --- #

    def first(self) -> ElementResponse:
        """Finds the first element matching the locator chain."""
        payload = ChainedRequest(selector_chain=self._selector_chain)
        return self._client._make_request("/first", payload, ElementResponse)

    def all(self) -> ElementsResponse:
        """Finds all elements matching the last selector in the chain."""
        payload = ChainedRequest(selector_chain=self._selector_chain)
        return self._client._make_request("/all", payload, ElementsResponse)

    def click(self) -> ClickResponse:
        """Clicks the element."""
        payload = ChainedRequest(selector_chain=self._selector_chain)
        return self._client._make_request("/click", payload, ClickResponse)

    def type_text(self, text: str) -> BasicResponse:
        """Types text into the element."""
        payload = TypeTextRequest(selector_chain=self._selector_chain, text=text)
        return self._client._make_request("/type_text", payload, BasicResponse)

    def get_text(self, max_depth: Optional[int] = None) -> TextResponse:
        """Gets the text content of the element."""
        payload = GetTextRequest(selector_chain=self._selector_chain, max_depth=max_depth)
        return self._client._make_request("/get_text", payload, TextResponse)

    def get_attributes(self) -> AttributesResponse:
        """Gets the attributes of the element."""
        payload = ChainedRequest(selector_chain=self._selector_chain)
        return self._client._make_request("/get_attributes", payload, AttributesResponse)

    def get_bounds(self) -> BoundsResponse:
        """Gets the bounding rectangle of the element."""
        payload = ChainedRequest(selector_chain=self._selector_chain)
        return self._client._make_request("/get_bounds", payload, BoundsResponse)

    def is_visible(self) -> bool:
        """Checks if the element is currently visible."""
        payload = ChainedRequest(selector_chain=self._selector_chain)
        response = self._client._make_request("/is_visible", payload, BooleanResponse)
        return response.result

    def press_key(self, key: str) -> BasicResponse:
        """Sends key presses to the element."""
        payload = PressKeyRequest(selector_chain=self._selector_chain, key=key)
        return self._client._make_request("/press_key", payload, BasicResponse)

    def activate_app(self) -> 'Locator':
        """
        Activates the application window associated with the element.

        This typically brings the window to the foreground.
        Waits for the element first (handled server-side).

        Returns:
            The current Locator instance to allow for method chaining.
        Raises:
            ApiError: If the server fails to activate the application window.
        """
        payload = ChainedRequest(selector_chain=self._selector_chain)
        # Calls the new /activate_app endpoint
        self._client._make_request("/activate_app", payload, BasicResponse)
        return self # Return self for chaining

    # --- Expectation Methods --- #

    def expect_visible(self, timeout: Optional[int] = None) -> ElementResponse:
        """
        Waits for the element to be visible.

        Args:
            timeout: Optional timeout in milliseconds.

        Returns:
            ElementResponse if visible within timeout.
        Raises:
            ApiError: If timeout occurs or another error happens.
        """
        payload = ExpectRequest(selector_chain=self._selector_chain, timeout_ms=timeout)
        return self._client._make_request("/expect_visible", payload, ElementResponse)

    def expect_enabled(self, timeout: Optional[int] = None) -> ElementResponse:
        """
        Waits for the element to be enabled.

        Args:
            timeout: Optional timeout in milliseconds.

        Returns:
            ElementResponse if enabled within timeout.
        Raises:
            ApiError: If timeout occurs or another error happens.
        """
        payload = ExpectRequest(selector_chain=self._selector_chain, timeout_ms=timeout)
        return self._client._make_request("/expect_enabled", payload, ElementResponse)

    def expect_text_equals(
        self,
        expected_text: str,
        max_depth: Optional[int] = None,
        timeout: Optional[int] = None
    ) -> ElementResponse:
        """
        Waits for the element's text to equal the expected value.

        Args:
            expected_text: The exact text to match.
            max_depth: Optional depth for text retrieval.
            timeout: Optional timeout in milliseconds.

        Returns:
            ElementResponse if text matches within timeout.
        Raises:
            ApiError: If timeout occurs, text doesn't match, or another error happens.
        """
        payload = ExpectTextRequest(
            selector_chain=self._selector_chain,
            expected_text=expected_text,
            max_depth=max_depth,
            timeout_ms=timeout
        )
        return self._client._make_request("/expect_text_equals", payload, ElementResponse)

# Helper function (can be part of the SDK or used externally)
def sleep(seconds: float) -> None:
    """Pauses execution for a specified number of seconds."""
    time.sleep(seconds) 
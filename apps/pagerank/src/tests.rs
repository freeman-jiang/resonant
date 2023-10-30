#[cfg(test)]
mod tests {
    use super::*;
    use crate::Node;

    #[test]
    fn test_preprocess_url() {
        let test_cases = vec![
            ("http://www.google.com", "google.com"),
            ("https://www.google.com", "google.com"),
            ("www.google.com", "google.com"),
            ("google.com", "google.com"),
            ("http://www.google.com?q=test", "google.com"),
            (
                "http://www.google.com/search/abc?q=test",
                "google.com/search/abc",
            ),
        ];

        for (input, expected) in test_cases {
            assert_eq!(Node::preprocess_url(input.to_string()), expected);
        }
    }
}

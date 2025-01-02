template <typename KA, typename T>
struct key_comparator {
    int operator()(const KA& ka, const T& n, int p) const {
        return n.get_key(p).compare(ka);
    }
}; 
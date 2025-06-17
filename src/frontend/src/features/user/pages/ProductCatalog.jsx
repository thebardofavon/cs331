import React, { useState, useEffect, useMemo } from "react";
import {
  Container,
  Typography,
  Grid,
  Box,
  Card,
  CardMedia,
  CardContent,
  Button,
  IconButton,
  TextField,
  InputAdornment,
  MenuItem,
  FormControl,
  Select,
  Chip,
  Skeleton,
  Breadcrumbs,
  Pagination,
  Dialog,
  DialogContent,
  DialogTitle,
  useMediaQuery,
  alpha,
  Slider,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Drawer,
  Divider
} from "@mui/material";
import {
  Search,
  FavoriteBorder,
  Favorite,
  ShoppingCart,
  GridView,
  ViewList,
  Close,
  Visibility,
  KeyboardArrowUp,
  ArrowForward,
  FilterList,
  ExpandMore,
  Clear
} from "@mui/icons-material";
import { ThemeProvider, createTheme, styled } from "@mui/material/styles";
import { useNavigate, Link as RouterLink, useSearchParams } from "react-router-dom";

// Create a more elegant, westside-inspired theme
const theme = createTheme({
  palette: {
    primary: {
      main: "#3a3a3a", // Subtle dark gray
      light: "#5c5c5c",
      dark: "#262626",
      contrastText: "#ffffff",
    },
    secondary: {
      main: "#f5f5f5", // Light gray
      light: "#ffffff",
      dark: "#e0e0e0",
      contrastText: "#3a3a3a",
    },
    background: {
      default: "#ffffff",
      paper: "#ffffff",
    },
    text: {
      primary: "#202020",
      secondary: "#616161",
    },
  },
  typography: {
    fontFamily: "'Inter', 'Helvetica Neue', 'Arial', sans-serif",
    h1: { fontWeight: 300 },
    h2: { fontWeight: 300 },
    h3: { fontWeight: 400 },
    h4: { fontWeight: 400 },
    h5: { fontWeight: 400 },
    h6: { fontWeight: 500 },
    button: {
      textTransform: "none",
      fontWeight: 500,
    },
  },
  shape: {
    borderRadius: 4,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          boxShadow: "none",
          "&:hover": { boxShadow: "none" },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: "none",
          transition: "box-shadow 0.3s ease",
          "&:hover": { boxShadow: "0 4px 12px rgba(0, 0, 0, 0.08)" },
        },
      },
    },
  },
});

// Refined styled components
const ProductCard = styled(Card)(({ theme }) => ({
  height: "100%",
  display: "flex",
  flexDirection: "column",
  position: "relative",
  transition: "all 0.3s ease",
  overflow: "hidden",
  background: "transparent",
  border: "none",
  "&:hover": {
    "& .product-image": {
      transform: "scale(1.04)",
    },
    "& .product-actions": {
      opacity: 1,
    },
    "& .hover-overlay": {
      opacity: 0.1,
    },
  },
}));

const ProductImage = styled(CardMedia)(({ theme }) => ({
  height: 400,
  transition: "transform 0.6s ease",
  position: "relative",
  objectFit: "cover",
}));

const ProductActions = styled(Box)(({ theme }) => ({
  position: "absolute",
  bottom: 16,
  left: 0,
  right: 0,
  display: "flex",
  justifyContent: "center",
  opacity: 0,
  transition: "all 0.3s ease",
  gap: 8,
  padding: "8px 0",
  zIndex: 2,
}));

const ImageOverlay = styled(Box)(({ theme }) => ({
  position: "absolute",
  top: 0,
  left: 0,
  right: 0,
  bottom: 0,
  backgroundColor: theme.palette.common.black,
  opacity: 0,
  transition: "opacity 0.3s ease",
  zIndex: 1,
}));

const ProductBadge = styled(Chip)(({ theme }) => ({
  position: "absolute",
  top: 12,
  left: 12,
  fontWeight: 500,
  fontSize: "0.75rem",
  letterSpacing: "0.5px",
  zIndex: 2,
}));

const SearchField = styled(TextField)(({ theme }) => ({
  "& .MuiOutlinedInput-root": {
    backgroundColor: theme.palette.background.paper,
    transition: "box-shadow 0.3s ease",
    "&:hover": { boxShadow: "0 2px 8px rgba(0,0,0,0.05)" },
    "&.Mui-focused": { boxShadow: "0 4px 12px rgba(0,0,0,0.08)" },
  },
}));

const StickyFilters = styled(Box)(({ theme }) => ({
  position: "sticky",
  top: 24,
  padding: theme.spacing(3),
  borderRadius: theme.shape.borderRadius,
  border: `1px solid ${alpha(theme.palette.divider, 0.6)}`,
  height: "fit-content", // Added to prevent stretching
}));

// Product Quick View dialog component
const QuickViewDialog = ({ open, onClose, product }) => {
  const fullScreen = useMediaQuery(theme.breakpoints.down("sm"));
  
  if (!product) return null;
  
  return (
    <Dialog
      open={open}
      onClose={onClose}
      fullScreen={fullScreen}
      maxWidth="md"
      PaperProps={{
        elevation: 2,
        sx: { borderRadius: 2, overflow: "hidden" }
      }}
    >
      <DialogTitle sx={{ 
        display: "flex", 
        justifyContent: "space-between",
        alignItems: "center",
        borderBottom: "1px solid",
        borderColor: "divider",
        pt: 2,
        pb: 2,
      }}>
        <Typography variant="h6" sx={{ fontWeight: 500 }}>Quick View</Typography>
        <IconButton onClick={onClose} size="small" sx={{ color: "text.secondary" }}>
          <Close fontSize="small" />
        </IconButton>
      </DialogTitle>
      <DialogContent>
        <Grid container>
          <Grid item xs={12} md={6}>
            <Box sx={{ position: "relative", height: "100%" }}>
              <Box
                component="img"
                src={`http://localhost:8000${product.image_url}`}
                alt={product.productDisplayName}
                sx={{
                  width: "100%",
                  height: "100%",
                  objectFit: "cover",
                  display: "block",
                  minHeight: { xs: 300, md: 480 },
                }}
              />
              {product.onSale && (
                <Chip
                  label="SALE"
                  color="error"
                  size="small"
                  sx={{
                    position: "absolute",
                    top: 16,
                    left: 16,
                    fontWeight: 500,
                  }}
                />
              )}
            </Box>
          </Grid>
          <Grid item xs={12} md={6}>
            <Box sx={{ p: 4, height: "100%", display: "flex", flexDirection: "column" }}>
              <Typography variant="caption" color="text.secondary" gutterBottom letterSpacing={0.8} textTransform="uppercase">
                {product.subCategory}
              </Typography>
              <Typography variant="h5" component="h2" gutterBottom sx={{ fontWeight: 400, mt: 1 }}>
                {product.productDisplayName}
              </Typography>
              
              <Typography variant="h5" color="text.primary" sx={{ mt: 2, mb: 0.5, fontWeight: 500 }}>
                ₹{product.price.toFixed(2)}
              </Typography>
              {product.oldPrice && (
                <Typography 
                  variant="body2" 
                  color="text.secondary" 
                  sx={{ textDecoration: "line-through", mb: 2 }}
                >
                  ₹{product.oldPrice.toFixed(2)}
                </Typography>
              )}
              <Typography variant="body2" color="text.secondary" sx={{ mb: 4, mt: 2, lineHeight: 1.7 }}>
                {product.description || "This premium product combines style, comfort, and quality craftsmanship. Made with carefully selected materials for everyday wear and special occasions alike."}
              </Typography>
              <Grid container spacing={2} sx={{ mb: 3, mt: 1 }}>
                <Grid item xs={12}>
                  <Button 
                    fullWidth 
                    variant="contained" 
                    color="primary"
                    startIcon={<ShoppingCart />}
                    sx={{ height: 48 }}
                  >
                    Add to Cart
                  </Button>
                </Grid>
                <Grid item xs={12}>
                  <Button 
                    fullWidth 
                    variant="outlined" 
                    color="primary"
                    startIcon={<FavoriteBorder />}
                    sx={{ height: 48 }}
                  >
                    Add to Wishlist
                  </Button>
                </Grid>
              </Grid>
              <Button 
                variant="text" 
                color="primary" 
                endIcon={<ArrowForward />}
                onClick={() => window.location.href = `/product/${product.id}`}
                sx={{ alignSelf: "center", mt: "auto" }}
              >
                View Full Details
              </Button>
            </Box>
          </Grid>
        </Grid>
      </DialogContent>
    </Dialog>
  );
};

// Filter panel component
const FilterPanel = ({ 
  genderFilter, 
  categoryFilter, 
  colorFilter, 
  priceRange, 
  priceRangeLimits, 
  sortBy,
  handleGenderChange, 
  handleCategoryChange, 
  handleColorChange, 
  handlePriceRangeChange, 
  setSortBy,
  handleClearFilters,
  availableFilters,
  activeFilters
}) => (
  <StickyFilters>
    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
      <Typography variant="h6" sx={{ fontWeight: 500 }}>
        Filters
      </Typography>
      
      {activeFilters.length > 0 && (
        <Button 
          size="small"
          startIcon={<Clear />}
          onClick={handleClearFilters}
          color="primary"
          sx={{ fontSize: '0.8rem' }}
        >
          Clear All
        </Button>
      )}
    </Box>
    
    {/* Gender Filter */}
    <Accordion 
      defaultExpanded 
      elevation={0} 
      sx={{ mb: 2, '&::before': { display: 'none' }, border: 'none' }}
    >
      <AccordionSummary 
        expandIcon={<ExpandMore />}
        sx={{ px: 0, '& .MuiAccordionSummary-content': { margin: 0 } }}
      >
        <Typography fontWeight={500}>Gender</Typography>
      </AccordionSummary>
      <AccordionDetails sx={{ px: 0 }}>
        <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
          {['Men', 'Women', 'Boys', 'Girls', 'Unisex'].map((gender) => (
            <Button
              key={gender}
              variant="text"
              color={genderFilter === gender ? "primary" : "inherit"}
              sx={{
                justifyContent: "flex-start",
                fontWeight: genderFilter === gender ? 600 : 400,
                py: 0.5,
                "&:hover": { backgroundColor: "transparent" },
                fontSize: '0.9rem',
              }}
              onClick={() => handleGenderChange(gender === genderFilter ? "" : gender)}
            >
              {gender}
            </Button>
          ))}
        </Box>
      </AccordionDetails>
    </Accordion>
    
    {/* Category Filter */}
    <Accordion 
      defaultExpanded 
      elevation={0} 
      sx={{ mb: 2, '&::before': { display: 'none' }, border: 'none' }}
    >
      <AccordionSummary 
        expandIcon={<ExpandMore />}
        sx={{ px: 0, '& .MuiAccordionSummary-content': { margin: 0 } }}
      >
        <Typography fontWeight={500}>Category</Typography>
      </AccordionSummary>
      <AccordionDetails sx={{ px: 0 }}>
        <Box sx={{ display: "flex", flexDirection: "column", gap: 1, maxHeight: 300, overflow: 'auto' }}>
          <Button
            variant="text"
            color={categoryFilter === "all" ? "primary" : "inherit"}
            sx={{
              justifyContent: "flex-start",
              fontWeight: categoryFilter === "all" ? 600 : 400,
              py: 0.5,
              "&:hover": { backgroundColor: "transparent" },
              fontSize: '0.9rem',
            }}
            onClick={() => handleCategoryChange("all")}
          >
            All Categories
          </Button>
          
          {/* Simplified master categories */}
          {availableFilters.masterCategory.map((masterCat) => (
            <Box key={masterCat} sx={{ mb: 1 }}>
              <Button
                variant="text"
                color={categoryFilter === masterCat ? "primary" : "inherit"}
                sx={{
                  justifyContent: "flex-start",
                  fontWeight: categoryFilter === masterCat ? 600 : 500,
                  py: 0.5,
                  "&:hover": { backgroundColor: "transparent" },
                  fontSize: '0.9rem',
                }}
                onClick={() => handleCategoryChange(masterCat)}
              >
                {masterCat}
              </Button>
              
              {/* Limited subcategories */}
              <Box sx={{ pl: 2 }}>
                {availableFilters.subCategory
                  .filter(subCat => subCat.includes(masterCat) || Math.random() > 0.7)
                  .slice(0, 5) // Limiting to 5 subcategories per master category
                  .map((subCat) => (
                    <Button
                      key={subCat}
                      variant="text"
                      color={categoryFilter === subCat ? "primary" : "inherit"}
                      sx={{
                        justifyContent: "flex-start",
                        fontWeight: categoryFilter === subCat ? 600 : 400,
                        py: 0.5,
                        "&:hover": { backgroundColor: "transparent" },
                        fontSize: '0.85rem'
                      }}
                      onClick={() => handleCategoryChange(subCat)}
                    >
                      {subCat}
                    </Button>
                  ))
                }
              </Box>
            </Box>
          ))}
        </Box>
      </AccordionDetails>
    </Accordion>
    
    {/* Color Filter */}
    <Accordion 
      defaultExpanded 
      elevation={0} 
      sx={{ mb: 2, '&::before': { display: 'none' }, border: 'none' }}
    >
      <AccordionSummary 
        expandIcon={<ExpandMore />}
        sx={{ px: 0, '& .MuiAccordionSummary-content': { margin: 0 } }}
      >
        <Typography fontWeight={500}>Color</Typography>
      </AccordionSummary>
      <AccordionDetails sx={{ px: 0 }}>
        <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5, maxHeight: 200, overflow: 'auto' }}>
          {availableFilters.baseColour.map((color) => (
            <Chip
              key={color}
              label={color}
              clickable
              onClick={() => handleColorChange(color === colorFilter ? "" : color)}
              color={colorFilter === color ? "primary" : "default"}
              variant={colorFilter === color ? "filled" : "outlined"}
              sx={{ m: 0.5 }}
            />
          ))}
        </Box>
      </AccordionDetails>
    </Accordion>
    
    {/* Price Range Filter */}
    <Accordion 
      defaultExpanded 
      elevation={0} 
      sx={{ mb: 2, '&::before': { display: 'none' }, border: 'none' }}
    >
      <AccordionSummary 
        expandIcon={<ExpandMore />}
        sx={{ px: 0, '& .MuiAccordionSummary-content': { margin: 0 } }}
      >
        <Typography fontWeight={500}>Price Range</Typography>
      </AccordionSummary>
      <AccordionDetails sx={{ px: 0 }}>
        <Box sx={{ px: 1 }}>
          <Slider
            value={priceRange}
            onChange={handlePriceRangeChange}
            valueLabelDisplay="auto"
            min={priceRangeLimits.min}
            max={priceRangeLimits.max}
            sx={{ mt: 4 }}
          />
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
            <Typography variant="body2" color="text.secondary">${priceRange[0]}</Typography>
            <Typography variant="body2" color="text.secondary">${priceRange[1]}</Typography>
          </Box>
        </Box>
      </AccordionDetails>
    </Accordion>
    
    {/* Sort By */}
    <Box sx={{ pt: 2 }}>
      <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 500, mb: 2 }}>
        Sort By
      </Typography>
      <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
        {[
          { value: "featured", label: "Featured" },
          { value: "priceAsc", label: "Price: Low to High" },
          { value: "priceDesc", label: "Price: High to Low" },
          { value: "nameAsc", label: "Name: A to Z" },
          { value: "nameDesc", label: "Name: Z to A" }
        ].map((option) => (
          <Button
            key={option.value}
            variant="text"
            color={sortBy === option.value ? "primary" : "inherit"}
            sx={{
              justifyContent: "flex-start",
              fontWeight: sortBy === option.value ? 600 : 400,
              py: 0.5,
              "&:hover": { backgroundColor: "transparent" },
              fontSize: '0.9rem',
            }}
            onClick={() => setSortBy(option.value)}
          >
            {option.label}
          </Button>
        ))}
      </Box>
    </Box>
  </StickyFilters>
);

// Main enhanced product catalog component
const ProductCatalog = () => {
  // URL Search Parameters
  const [searchParams, setSearchParams] = useSearchParams();
  
  // State management - initializing from URL params where available
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState(searchParams.get("search") || "");
  const [sortBy, setSortBy] = useState(searchParams.get("sort_by") || "featured");
  const [categoryFilter, setCategoryFilter] = useState(searchParams.get("category") || "all");
  const [genderFilter, setGenderFilter] = useState(searchParams.get("gender") || "");
  const [colorFilter, setColorFilter] = useState(searchParams.get("color") || "");
  const [priceRange, setPriceRange] = useState([
    parseFloat(searchParams.get("price_min")) || 0, 
    parseFloat(searchParams.get("price_max")) || 1000
  ]);
  const [viewMode, setViewMode] = useState(searchParams.get("view") || "grid");
  const [page, setPage] = useState(parseInt(searchParams.get("page")) || 1);
  const [quickViewProduct, setQuickViewProduct] = useState(null);
  const [showBackToTop, setShowBackToTop] = useState(false);
  const [wishlist, setWishlist] = useState([]);
  const [mobileFiltersOpen, setMobileFiltersOpen] = useState(false);
  const [productsPerPage, setProductsPerPage] = useState(parseInt(searchParams.get("limit")) || 12);
  const [totalProducts, setTotalProducts] = useState(0);
  const [availableFilters, setAvailableFilters] = useState({
    gender: [],
    masterCategory: [],
    subCategory: [],
    articleType: [],
    baseColour: [],
    season: [],
    usage: [],
  });
  const [priceRangeLimits, setPriceRangeLimits] = useState({ min: 0, max: 1000 });
  const [activeFilters, setActiveFilters] = useState([]);
  
  const navigate = useNavigate();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  // Calculate offset for API pagination
  const offset = (page - 1) * productsPerPage;

  // Track scroll for back-to-top button
  useEffect(() => {
    const handleScroll = () => {
      setShowBackToTop(window.scrollY > 500);
    };
    
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // Fetch available filters for filter dropdowns
  useEffect(() => {
    const fetchFilters = async () => {
      try {
        const [categoriesResponse, priceRangeResponse] = await Promise.all([
          fetch("http://localhost:8000/api/categories"),
          fetch("http://localhost:8000/api/price-range")
        ]);
        
        if (!categoriesResponse.ok || !priceRangeResponse.ok) {
          throw new Error(`Failed to fetch filters`);
        }
        
        const categories = await categoriesResponse.json();
        const priceRange = await priceRangeResponse.json();
        
        setAvailableFilters(categories);
        setPriceRangeLimits({
          min: Math.floor(priceRange.min_price),
          max: Math.ceil(priceRange.max_price)
        });
        
        // Initialize price range if not already set
        if (priceRange.min_price !== undefined && priceRange.max_price !== undefined && 
            !searchParams.has("price_min") && !searchParams.has("price_max")) {
          setPriceRange([
            Math.floor(priceRange.min_price),
            Math.ceil(priceRange.max_price)
          ]);
        }
      } catch (err) {
        console.error("Error fetching filters:", err);
      }
    };

    fetchFilters();
  }, [searchParams]);

  // Update active filters display
  useEffect(() => {
    const newActiveFilters = [];
    
    if (categoryFilter && categoryFilter !== "all") {
      newActiveFilters.push({ type: "category", value: categoryFilter, label: `Category: ${categoryFilter}` });
    }
    
    if (genderFilter) {
      newActiveFilters.push({ type: "gender", value: genderFilter, label: `Gender: ${genderFilter}` });
    }
    
    if (colorFilter) {
      newActiveFilters.push({ type: "color", value: colorFilter, label: `Color: ${colorFilter}` });
    }
    
    if (priceRange[0] > priceRangeLimits.min || priceRange[1] < priceRangeLimits.max) {
      newActiveFilters.push({ 
        type: "price", 
        value: priceRange, 
        label: `Price: ₹${priceRange[0]} - ₹${priceRange[1]}` 
      });
    }
    
    if (searchQuery) {
      newActiveFilters.push({ type: "search", value: searchQuery, label: `Search: ${searchQuery}` });
    }
    
    setActiveFilters(newActiveFilters);
  }, [categoryFilter, genderFilter, colorFilter, priceRange, searchQuery, priceRangeLimits]);

  // Update URL params when filters change
  useEffect(() => {
    const params = new URLSearchParams();
    
    if (page > 1) params.set("page", page.toString());
    if (searchQuery) params.set("search", searchQuery);
    if (sortBy !== "featured") params.set("sort_by", sortBy);
    if (categoryFilter !== "all") params.set("category", categoryFilter);
    if (genderFilter) params.set("gender", genderFilter);
    if (colorFilter) params.set("color", colorFilter);
    if (priceRange[0] > priceRangeLimits.min) params.set("price_min", priceRange[0].toString());
    if (priceRange[1] < priceRangeLimits.max) params.set("price_max", priceRange[1].toString());
    if (viewMode !== "grid") params.set("view", viewMode);
    if (productsPerPage !== 12) params.set("limit", productsPerPage.toString());
    
    setSearchParams(params);
  }, [
    page, 
    searchQuery, 
    sortBy, 
    categoryFilter, 
    genderFilter, 
    colorFilter, 
    priceRange, 
    viewMode, 
    productsPerPage, 
    priceRangeLimits,
    setSearchParams
  ]);

  // Fetch products from API with all filters applied
  useEffect(() => {
    const fetchProducts = async (retryCount = 0) => {
      setLoading(true);
      setError(null);
      
      try {
        // Build query parameters
        const params = new URLSearchParams();
        params.append("limit", productsPerPage.toString());
        params.append("offset", offset.toString());
        
        if (searchQuery) params.append("search", searchQuery);
        
        if (categoryFilter && categoryFilter !== "all") {
          // Determine which filter to use based on the category value 
          if (availableFilters.articleType.includes(categoryFilter)) {
            params.append("articleType", categoryFilter);
          } else if (availableFilters.subCategory.includes(categoryFilter)) {
            params.append("subCategory", categoryFilter);
          } else if (availableFilters.masterCategory.includes(categoryFilter)) {
            params.append("masterCategory", categoryFilter);
          }
        }
        
        if (genderFilter) params.append("gender", genderFilter);
        if (colorFilter) params.append("baseColour", colorFilter);
        
        if (priceRange[0] > priceRangeLimits.min) params.append("price_min", priceRange[0].toString());
        if (priceRange[1] < priceRangeLimits.max) params.append("price_max", priceRange[1].toString());
        
        // Map UI sort options to API sort parameters
        switch(sortBy) {
          case "priceAsc":
            params.append("sort_by", "price");
            params.append("sort_direction", "asc");
            break;
          case "priceDesc":
            params.append("sort_by", "price");
            params.append("sort_direction", "desc");
            break;
          case "nameAsc":
            params.append("sort_by", "productDisplayName");
            params.append("sort_direction", "asc");
            break;
          case "nameDesc":
            params.append("sort_by", "productDisplayName");
            params.append("sort_direction", "desc");
            break;
          default: // featured
            params.append("sort_by", "id");
            params.append("sort_direction", "asc");
            break;
        }
        
        const response = await fetch(`http://localhost:8000/api/products?${params.toString()}`);
        
        if (!response.ok) {
          // If it's a 500 error and we've not retried too many times, try again
          if (response.status === 500 && retryCount < 2) {
            console.log(`Retrying fetch (attempt ${retryCount + 1})...`);
            setTimeout(() => fetchProducts(retryCount + 1), 1500);
            return;
          }
          throw new Error(`Failed to fetch: ${response.status}`);
        }

        const data = await response.json();
        
        // Get total count from header if available
        const totalCount = response.headers.get("X-Total-Count");
        if (totalCount) {
          setTotalProducts(parseInt(totalCount));
        } else {
          // If no header, estimate based on current page
          setTotalProducts(Math.max((page * productsPerPage), data.products.length + offset));
        }
        
        // Process products to ensure all have required fields
        const processedProducts = data.products.map((product, index) => ({
          ...product,
          price: product.price || Math.floor(Math.random() * 100) + 20,
          oldPrice: index % 3 === 0 ? (product.price || Math.floor(Math.random() * 100) + 20) * 1.2 : null,
          image_url: product.image_url || "/images/placeholder.jpg",
          productDisplayName: product.productDisplayName || "Untitled Product",
          subCategory: product.subCategory || "Uncategorized",
          rating: (Math.random() * 2 + 3).toFixed(1),
          reviewCount: Math.floor(Math.random() * 500) + 10,
          onSale: index % 4 === 0,
          isNew: index % 5 === 0,
        }));

        setProducts(processedProducts);
      } catch (err) {
        console.error("Error fetching products:", err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchProducts();
  }, [
    productsPerPage, 
    offset, 
    searchQuery, 
    sortBy, 
    categoryFilter, 
    genderFilter, 
    colorFilter, 
    priceRange,
    availableFilters,
    page,
    priceRangeLimits
  ]);

  // Get unique categories for filtering
  const categories = useMemo(() => {
    const allCategories = [
      ...availableFilters.masterCategory,
      ...availableFilters.subCategory,
      ...availableFilters.articleType
    ];
    // Remove duplicates
    return ['all', ...new Set(allCategories)];
  }, [availableFilters]);

  // Event handlers
  const toggleWishlist = (productId) => {
    setWishlist(prev => 
      prev.includes(productId)
        ? prev.filter(id => id !== productId)
        : [...prev, productId]
    );
  };

  const handleQuickView = (e, product) => {
    e.stopPropagation();
    setQuickViewProduct(product);
  };

  const handleCloseQuickView = () => {
    setQuickViewProduct(null);
  };

  const handleCategoryChange = (category) => {
    setCategoryFilter(category);
    setPage(1); // Reset to first page when changing filters
  };

  const handleGenderChange = (gender) => {
    setGenderFilter(gender);
    setPage(1);
  };

  const handleColorChange = (color) => {
    setColorFilter(color);
    setPage(1);
  };

  const handlePriceRangeChange = (event, newValue) => {
    setPriceRange(newValue);
    setPage(1);
  };

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1); // Reset to first page on new search
  };

  const toggleMobileFilters = () => {
    setMobileFiltersOpen(!mobileFiltersOpen);
  };

  const handleClearFilters = () => {
    setSearchQuery("");
    setSortBy("featured");
    setCategoryFilter("all");
    setGenderFilter("");
    setColorFilter("");
    setPriceRange([priceRangeLimits.min, priceRangeLimits.max]);
    setPage(1);
  };

  const handleRemoveFilter = (filter) => {
    switch (filter.type) {
      case "category":
        setCategoryFilter("all");
        break;
      case "gender":
        setGenderFilter("");
        break;
      case "color":
        setColorFilter("");
        break;
      case "price":
        setPriceRange([priceRangeLimits.min, priceRangeLimits.max]);
        break;
      case "search":
        setSearchQuery("");
        break;
      default:
        break;
    }
  };

  // Create skeleton loader for products
  const ProductSkeleton = () => (
    <Card sx={{ height: '100%', boxShadow: 'none' }}>
      <Skeleton variant="rectangular" height={380} sx={{ borderRadius: 1 }} />
      <CardContent sx={{ pt: 2, px: 0 }}>
        <Skeleton variant="text" width="60%" height={24} />
        <Skeleton variant="text" width="40%" height={20} />
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
          <Skeleton variant="text" width="30%" height={32} />
          <Skeleton variant="circular" width={36} height={36} />
        </Box>
      </CardContent>
    </Card>
  );

  return (
    <ThemeProvider theme={theme}>
      <Box sx={{ 
        bgcolor: "background.default", 
        minHeight: "100vh", 
        pb: 8, 
        px: { xs: 2, md: 4, lg: 6 }, 
        pt: { xs: 4, md: 6 }
      }}>
        {/* Hero section */}
        <Box
          sx={{
            bgcolor: "#f8f8f8",
            color: "text.primary",
            py: { xs: 6, md: 10 },
            px: { xs: 3, md: 6 },
            mb: 6,
            borderRadius: 1,
            position: "relative",
            overflow: "hidden",
          }}
        >
          <Container maxWidth="xl">
            <Grid container spacing={4}>
              <Grid item xs={12} md={7} lg={6}>
                <Box>
                  <Typography 
                    variant="caption" 
                    sx={{ 
                      fontWeight: 500, 
                      letterSpacing: 2,
                      textTransform: "uppercase",
                      display: "block",
                      mb: 1,
                      color: "primary.main"
                    }}
                  >
                    Spring Collection 2025
                  </Typography>
                  <Typography
                    variant="h2"
                    component="h1"
                    sx={{
                      fontWeight: 300,
                      mb: 3,
                      letterSpacing: "-0.5px",
                      fontSize: { xs: "2rem", md: "3rem" },
                    }}
                  >
                    Timeless Elegance
                  </Typography>
                  <Typography 
                    variant="body1" 
                    sx={{ 
                      fontWeight: 400, 
                      mb: 4,
                      maxWidth: 500,
                      lineHeight: 1.7,
                    }}
                  >
                    Discover our curated collection of sophisticated essentials designed for the modern wardrobe.
                  </Typography>
                  <Button 
                    variant="contained" 
                    color="primary"
                    size="large"
                    sx={{ py: 1.2, px: 3 }}
                  >
                    Explore Collection
                  </Button>
                </Box>
              </Grid>
            </Grid>
          </Container>
        </Box>

        <Container maxWidth="xl">
          {/* Breadcrumbs navigation */}
          <Breadcrumbs sx={{ mb: 4 }}>
            <Typography 
              component={RouterLink} 
              to="/" 
              color="inherit" 
              sx={{ 
                textDecoration: "none",
                "&:hover": { textDecoration: "underline" }
              }}
            >
              Home
            </Typography>
            <Typography color="text.primary">Products</Typography>
          </Breadcrumbs>

          {/* Main page layout */}
          <Box sx={{ display: "flex", flexDirection: { xs: "column", md: "row" }, gap: 4 }}>
            {/* Sidebar with filters - visible on desktop */}
            <Box 
              sx={{ 
                width: { md: '280px', lg: '320px' }, 
                flexShrink: 0, 
                display: { xs: "none", md: "block" }
              }}
            >
              <FilterPanel 
                genderFilter={genderFilter}
                categoryFilter={categoryFilter}
                colorFilter={colorFilter}
                priceRange={priceRange}
                priceRangeLimits={priceRangeLimits}
                sortBy={sortBy}
                handleGenderChange={handleGenderChange}
                handleCategoryChange={handleCategoryChange}
                handleColorChange={handleColorChange}
                handlePriceRangeChange={handlePriceRangeChange}
                setSortBy={setSortBy}
                handleClearFilters={handleClearFilters}
                availableFilters={availableFilters}
                activeFilters={activeFilters}
              />
            </Box>

            {/* Main content area */}
            <Box sx={{ flexGrow: 1, width: { xs: '100%', md: 'calc(100% - 300px)', lg: 'calc(100% - 340px)' } }}>
              {/* Search & filter bar */}
              <Box
                sx={{
                  mb: 4,
                  display: "flex",
                  flexWrap: "wrap",
                  gap: 2,
                  alignItems: "center",
                  justifyContent: "space-between",
                }}
              >
                <Box sx={{ display: "flex", alignItems: "center", gap: 2, flexGrow: 1 }}>
                  <form onSubmit={handleSearchSubmit} style={{ width: '100%', maxWidth: 300 }}>
                    <SearchField
                      placeholder="Search products..."
                      variant="outlined"
                      size="small"
                      fullWidth
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      InputProps={{
                        startAdornment: (
                          <InputAdornment position="start">
                            <Search color="action" />
                          </InputAdornment>
                        ),
                      }}
                    />
                  </form>
                  
                  {/* Mobile filter button */}
                  <Button
                    variant="outlined"
                    startIcon={<FilterList />}
                    size="small"
                    onClick={toggleMobileFilters}
                    sx={{ display: { md: 'none' } }}
                  >
                    Filters {activeFilters.length > 0 && `(${activeFilters.length})`}
                  </Button>
                </Box>
                
                <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
                  <Box sx={{ display: "flex", alignItems: "center" }}>
                    <IconButton
                      color={viewMode === "grid" ? "primary" : "default"}
                      onClick={() => setViewMode("grid")}
                      size="small"
                    >
                      <GridView fontSize="small" />
                    </IconButton>
                    <IconButton
                      color={viewMode === "list" ? "primary" : "default"}
                      onClick={() => setViewMode("list")}
                      size="small"
                      sx={{ display: { xs: "none", sm: "flex" } }}
                    >
                      <ViewList fontSize="small" />
                    </IconButton>
                  </Box>
                  
                  {/* Sort selector for mobile */}
                  <Box sx={{ display: { xs: "block", md: "none" } }}>
                    <FormControl size="small">
                      <Select
                        value={sortBy}
                        onChange={(e) => setSortBy(e.target.value)}
                        displayEmpty
                        size="small"
                      >
                        <MenuItem value="featured">Featured</MenuItem>
                        <MenuItem value="priceAsc">Price: Low to High</MenuItem>
                        <MenuItem value="priceDesc">Price: High to Low</MenuItem>
                        <MenuItem value="nameAsc">Name: A to Z</MenuItem>
                        <MenuItem value="nameDesc">Name: Z to A</MenuItem>
                      </Select>
                    </FormControl>
                  </Box>
                </Box>
              </Box>

              {/* Results count and active filters */}
              <Box
                sx={{
                  display: "flex",
                  flexDirection: { xs: 'column', sm: 'row' },
                  justifyContent: "space-between",
                  alignItems: { xs: 'flex-start', sm: 'center' },
                  flexWrap: 'wrap',
                  mb: 4,
                  gap: 2
                }}
              >
                <Typography variant="body2" color="text.secondary">
                  Showing {products.length} of {totalProducts} products
                </Typography>
                
                {activeFilters.length > 0 && (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {activeFilters.map((filter, index) => (
                      <Chip
                        key={index}
                        label={filter.label}
                        onDelete={() => handleRemoveFilter(filter)}
                        size="small"
                        color="primary"
                        variant="outlined"
                      />
                    ))}
                    
                    <Button 
                      size="small"
                      variant="text"
                      onClick={handleClearFilters}
                      sx={{ ml: 1, fontWeight: 500 }}
                    >
                      Clear All
                    </Button>
                  </Box>
                )}
              </Box>

              {loading ? (
                // Skeleton loading state
                <Grid container spacing={3}>
                  {Array.from(new Array(productsPerPage)).map((_, index) => (
                    <Grid item xs={12} sm={6} md={viewMode === "list" ? 12 : 6} lg={viewMode === "list" ? 12 : 4} key={index}>
                      <ProductSkeleton />
                    </Grid>
                  ))}
                </Grid>
              ) : error ? (
                // Error state
                <Box
                  sx={{
                    textAlign: "center",
                    py: 8,
                    px: 3,
                    border: '1px solid',
                    borderColor: 'divider',
                  }}
                >
                  <Typography variant="h5" gutterBottom sx={{ fontWeight: 400 }}>
                    Oops! Something went wrong
                  </Typography>
                  <Typography color="text.secondary" paragraph sx={{ mb: 4 }}>
                    {error}
                  </Typography>
                  <Button
                    variant="contained"
                    color="primary"
                    onClick={() => window.location.reload()}
                  >
                    Retry
                  </Button>
                </Box>
              ) : products.length === 0 ? (
                // No results state
                <Box
                  sx={{
                    textAlign: "center",
                    py: 8,
                    px: 3,
                    border: '1px solid',
                    borderColor: 'divider',
                  }}
                >
                  <Typography variant="h5" gutterBottom sx={{ fontWeight: 400 }}>
                    No products found
                  </Typography>
                  <Typography color="text.secondary" paragraph sx={{ mb: 4 }}>
                    Try adjusting your search or filter criteria.
                  </Typography>
                  <Button
                    variant="outlined"
                    color="primary"
                    onClick={handleClearFilters}
                  >
                    Clear Filters
                  </Button>
                </Box>
              ) : (
                // Product grid/list
                <>
                  <Grid container spacing={3}>
                    {products.map((product) => (
                      <Grid 
                        item 
                        xs={12} 
                        sm={viewMode === "list" ? 12 : 6} 
                        md={viewMode === "list" ? 12 : 6} 
                        lg={viewMode === "list" ? 12 : 4} 
                        key={product.id}
                      >
                        {viewMode === "grid" ? (
                          <ProductCard 
                            onClick={() => navigate(`/product/${product.id}`)}
                            sx={{ cursor: "pointer" }}
                          >
                            <Box sx={{ position: "relative", overflow: "hidden" }}>
                              {product.onSale && (
                                <ProductBadge
                                  label="SALE"
                                  color="error"
                                  size="small"
                                />
                              )}
                              {product.isNew && (
                                <ProductBadge
                                  label="NEW"
                                  size="small"
                                  sx={{ 
                                    top: product.onSale ? 54 : 12,
                                    backgroundColor: theme.palette.primary.main,
                                    color: "white"
                                  }}
                                />
                              )}
                              <ProductImage
                                component="img"
                                image={`http://localhost:8000${product.image_url}`}
                                alt={product.productDisplayName}
                                className="product-image"
                              />
                              <ImageOverlay className="hover-overlay" />
                              <ProductActions className="product-actions">
                                <Button
                                  variant="contained"
                                  color="primary"
                                  size="small"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    console.log(`Added ${product.id} to cart`);
                                  }}
                                  startIcon={<ShoppingCart />}
                                >
                                  Add to Cart
                                </Button>
                                <IconButton
                                  onClick={(e) => handleQuickView(e, product)}
                                  sx={{
                                    bgcolor: "white",
                                    "&:hover": { bgcolor: "white" },
                                    boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
                                  }}
                                >
                                  <Visibility fontSize="small" />
                                </IconButton>
                                <IconButton
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    toggleWishlist(product.id);
                                  }}
                                  sx={{
                                    bgcolor: "white",
                                    "&:hover": { bgcolor: "white" },
                                    boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
                                  }}
                                >
                                  {wishlist.includes(product.id) ? (
                                    <Favorite fontSize="small" color="error" />
                                  ) : (
                                    <FavoriteBorder fontSize="small" />
                                  )}
                                </IconButton>
                              </ProductActions>
                            </Box>
                            <CardContent sx={{ pt: 2.5, px: 1 }}>
                              <Typography
                                variant="caption"
                                color="text.secondary"
                                component="div"
                                letterSpacing={0.8}
                                sx={{ mb: 0.5 }}
                              >
                                {product.subCategory}
                              </Typography>
                              <Typography
                                variant="body2"
                                component="div"
                                noWrap
                                sx={{ fontWeight: 500, mb: 1 }}
                              >
                                {product.productDisplayName}
                              </Typography>
                              <Typography
                                variant="subtitle2"
                                color="text.primary"
                                sx={{ fontWeight: 600 }}
                              >
                                ₹{product.price.toFixed(2)}
                                {product.oldPrice && (
                                  <Typography
                                    component="span"
                                    variant="body2"
                                    color="text.secondary"
                                    sx={{ textDecoration: "line-through", ml: 1 }}
                                  >
                                    ₹{product.oldPrice.toFixed(2)}
                                  </Typography>
                                )}
                              </Typography>
                            </CardContent>
                          </ProductCard>
                        ) : (
                          // List view layout
                          <ProductCard sx={{ cursor: "pointer" }}>
                            <Box
                              sx={{
                                display: "flex",
                                flexDirection: { xs: "column", sm: "row" },
                              }}
                              onClick={() => navigate(`/product/${product.id}`)}
                            >
                              <Box sx={{ position: "relative", width: { xs: "100%", sm: 250 }, overflow: "hidden" }}>
                                {product.onSale && (
                                  <ProductBadge
                                    label="SALE"
                                    color="error"
                                    size="small"
                                  />
                                )}
                                {product.isNew && (
                                  <ProductBadge
                                    label="NEW"
                                    size="small"
                                    sx={{ 
                                      top: product.onSale ? 54 : 12,
                                      backgroundColor: theme.palette.primary.main,
                                      color: "white"
                                    }}
                                  />
                                )}
                                <ProductImage
                                  component="img"
                                  image={`http://localhost:8000${product.image_url}`}
                                  alt={product.productDisplayName}
                                  className="product-image"
                                  sx={{ 
                                    height: { xs: 200, sm: 300 },
                                    width: { xs: "100%", sm: 250 },
                                  }}
                                />
                                <ImageOverlay className="hover-overlay" />
                              </Box>
                              <Box sx={{ p: 3, flex: 1 }}>
                                <Typography
                                  variant="caption"
                                  color="text.secondary"
                                  letterSpacing={0.8}
                                  sx={{ display: "block", mb: 0.5 }}
                                >
                                  {product.subCategory}
                                </Typography>
                                <Typography
                                  variant="h6"
                                  component="div"
                                  sx={{ fontWeight: 500, mb: 1 }}
                                >
                                  {product.productDisplayName}
                                </Typography>
                                <Typography
                                  variant="body2"
                                  color="text.secondary"
                                  sx={{ mb: 3, display: { xs: "none", md: "block" }, lineHeight: 1.7 }}
                                >
                                  {product.description || 
                                    "This premium product combines style and comfort with quality craftsmanship."}
                                </Typography>
                                <Box
                                  sx={{
                                    display: "flex",
                                    justifyContent: "space-between",
                                    alignItems: "center",
                                    mt: "auto",
                                    flexWrap: { xs: "wrap", md: "nowrap" },
                                    gap: 2
                                  }}
                                >
                                  <Typography
                                    variant="h6"
                                    color="text.primary"
                                    sx={{ fontWeight: 600 }}
                                  >
                                    ₹{product.price.toFixed(2)}
                                    {product.oldPrice && (
                                      <Typography
                                        component="span"
                                        variant="body2"
                                        color="text.secondary"
                                        sx={{ textDecoration: "line-through", ml: 1 }}
                                      >
                                        ₹{product.oldPrice.toFixed(2)}
                                      </Typography>
                                    )}
                                  </Typography>
                                  <Box sx={{ display: "flex", gap: 2 }}>
                                    <Button
                                      variant="outlined"
                                      color="primary"
                                      startIcon={<Visibility />}
                                      onClick={(e) => handleQuickView(e, product)}
                                    >
                                      Quick View
                                    </Button>
                                    <Button
                                      variant="contained"
                                      color="primary"
                                      startIcon={<ShoppingCart />}
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        console.log(`Added ${product.id} to cart`);
                                      }}
                                    >
                                      Add to Cart
                                    </Button>
                                  </Box>
                                </Box>
                              </Box>
                            </Box>
                          </ProductCard>
                        )}
                      </Grid>
                    ))}
                  </Grid>
                  
                  {/* Pagination controls */}
                  {totalProducts > productsPerPage && (
                    <Box
                      sx={{
                        display: "flex",
                        flexDirection: { xs: 'column', sm: 'row' },
                        justifyContent: "space-between",
                        alignItems: "center",
                        mt: 6,
                        mb: 2,
                        gap: 2
                      }}
                    >
                      <FormControl size="small" sx={{ minWidth: 120 }}>
                        <Select
                          value={productsPerPage}
                          onChange={(e) => {
                            setProductsPerPage(Number(e.target.value));
                            setPage(1); // Reset to first page when changing page size
                          }}
                          displayEmpty
                          size="small"
                          variant="outlined"
                        >
                          <MenuItem value={12}>12 per page</MenuItem>
                          <MenuItem value={24}>24 per page</MenuItem>
                          <MenuItem value={36}>36 per page</MenuItem>
                          <MenuItem value={48}>48 per page</MenuItem>
                        </Select>
                      </FormControl>
                      
                      <Pagination
                        count={Math.ceil(totalProducts / productsPerPage)}
                        page={page}
                        onChange={(e, newPage) => setPage(newPage)}
                        color="primary"
                        size={isMobile ? "medium" : "large"}
                        showFirstButton
                        showLastButton
                      />
                    </Box>
                  )}
                </>
              )}
            </Box>
          </Box>
        </Container>

        {/* Mobile Filters Drawer */}
        <Drawer
          anchor="left"
          open={mobileFiltersOpen}
          onClose={() => setMobileFiltersOpen(false)}
          PaperProps={{
            sx: { width: '80%', maxWidth: 350, pt: 0 }
          }}
        >
          <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid', borderColor: 'divider' }}>
            <Typography variant="h6" sx={{ fontWeight: 500 }}>Filters</Typography>
            <IconButton onClick={() => setMobileFiltersOpen(false)}>
              <Close fontSize="small" />
            </IconButton>
          </Box>
          
          <Box sx={{ p: 2, height: '100%', overflow: 'auto' }}>
            <FilterPanel 
              genderFilter={genderFilter}
              categoryFilter={categoryFilter}
              colorFilter={colorFilter}
              priceRange={priceRange}
              priceRangeLimits={priceRangeLimits}
              sortBy={sortBy}
              handleGenderChange={handleGenderChange}
              handleCategoryChange={handleCategoryChange}
              handleColorChange={handleColorChange}
              handlePriceRangeChange={handlePriceRangeChange}
              setSortBy={setSortBy}
              handleClearFilters={handleClearFilters}
              availableFilters={availableFilters}
              activeFilters={activeFilters}
            />
          </Box>
          
          <Box sx={{ p: 2, borderTop: '1px solid', borderColor: 'divider', display: 'flex', justifyContent: 'space-between' }}>
            <Button 
              variant="outlined" 
              color="inherit" 
              onClick={handleClearFilters}
            >
              Clear All
            </Button>
            <Button 
              variant="contained" 
              color="primary" 
              onClick={() => setMobileFiltersOpen(false)}
            >
              Apply Filters
            </Button>
          </Box>
        </Drawer>

        {/* Back to top button */}
        <Box
          onClick={scrollToTop}
          sx={{
            position: "fixed",
            bottom: 24,
            right: 24,
            zIndex: 10,
            cursor: "pointer",
            bgcolor: alpha(theme.palette.primary.main, 0.9),
            color: "white",
            width: 45,
            height: 45,
            display: showBackToTop ? "flex" : "none",
            alignItems: "center",
            justifyContent: "center",
            transition: "all 0.2s",
            borderRadius: "50%",
            boxShadow: "0 2px 8px rgba(0,0,0,0.2)",
            "&:hover": {
              bgcolor: theme.palette.primary.main,
              transform: "translateY(-3px)",
            },
          }}
        >
          <KeyboardArrowUp />
        </Box>

        {/* Quick view dialog */}
        <QuickViewDialog 
          open={!!quickViewProduct} 
          onClose={handleCloseQuickView} 
          product={quickViewProduct}
        />
      </Box>
    </ThemeProvider>
  );
};

export default ProductCatalog;